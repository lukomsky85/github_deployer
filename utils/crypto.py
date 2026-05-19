# utils/crypto.py
"""
Безопасное хранение GitHub токена.

Стратегия (в порядке приоритета):
  1. keyring  — системное хранилище ОС (Windows Credential Manager /
                macOS Keychain / Linux SecretService).
                Токен никогда не пишется на диск в файл приложения.
  2. Fernet   — шифрование AES-128 ключом привязанным к MAC-адресу машины.
                Fallback если keyring недоступен.
  3. Plaintext — последний резерв с явным предупреждением (не используется
                в production, только для отладки без зависимостей).
"""

import os
import base64
import hashlib
import uuid
import logging

logger = logging.getLogger(__name__)

# ── Зависимости (опциональные) ────────────────────────────────────────────────

try:
    import keyring
    import keyring.errors
    _KEYRING_AVAILABLE = True
except ImportError:
    _KEYRING_AVAILABLE = False

try:
    from cryptography.fernet import Fernet, InvalidToken
    _FERNET_AVAILABLE = True
except ImportError:
    _FERNET_AVAILABLE = False


# ── Константы ─────────────────────────────────────────────────────────────────

_KEYRING_SERVICE = "GitHubDeployHelper"
_KEYRING_USERNAME = "github_token"
_FERNET_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "secure_token.dat"
)
_SALT = "GDH_v4_salt_2025"


# ── Внутренние хелперы ────────────────────────────────────────────────────────

def _fernet_key() -> bytes:
    """Ключ Fernet привязан к MAC-адресу: разные машины — разные ключи."""
    try:
        machine_id = str(uuid.getnode())
    except Exception:
        machine_id = "fallback_machine"
    raw = hashlib.sha256((machine_id + _SALT).encode()).digest()
    return base64.urlsafe_b64encode(raw)


def _sanitize_token(token: str) -> str:
    """Убирает пробелы и переносы строк которые пользователь мог случайно вставить."""
    return token.strip()


def _mask_token(token: str) -> str:
    """Маскирует токен для безопасного логирования: ghp_AbCd...XyZ → ghp_****XyZ"""
    if not token or len(token) < 8:
        return "****"
    return token[:4] + "****" + token[-4:]


# ── Публичный API ─────────────────────────────────────────────────────────────

class TokenManager:
    """
    Единая точка входа для работы с токеном.
    Все методы статические — состояние хранится в ОС / файле, не в памяти.
    """

    # ── Сохранение ────────────────────────────────────────────────────────────

    @staticmethod
    def save_token(token: str) -> bool:
        """
        Сохраняет токен наиболее безопасным доступным способом.
        Возвращает True при успехе.
        """
        if not token:
            return False
        token = _sanitize_token(token)

        # 1. Системное хранилище (приоритет)
        if _KEYRING_AVAILABLE:
            try:
                keyring.set_password(_KEYRING_SERVICE, _KEYRING_USERNAME, token)
                # Если был старый файл Fernet — удаляем, keyring теперь главный
                TokenManager._remove_fernet_file()
                logger.debug("Token saved to system keyring (%s)", _mask_token(token))
                return True
            except Exception as e:
                logger.warning("keyring unavailable (%s), falling back to Fernet", e)

        # 2. Fernet
        if _FERNET_AVAILABLE:
            try:
                encrypted = Fernet(_fernet_key()).encrypt(token.encode("utf-8"))
                with open(_FERNET_FILE, "wb") as f:
                    f.write(encrypted)
                logger.debug("Token saved with Fernet (%s)", _mask_token(token))
                return True
            except Exception as e:
                logger.error("Fernet save failed: %s", e)

        logger.error("No secure storage available — token NOT saved")
        return False

    # ── Загрузка ──────────────────────────────────────────────────────────────

    @staticmethod
    def load_token() -> str | None:
        """
        Загружает токен. Пробует keyring → Fernet.
        Возвращает строку или None.
        """
        # 1. Системное хранилище
        if _KEYRING_AVAILABLE:
            try:
                token = keyring.get_password(_KEYRING_SERVICE, _KEYRING_USERNAME)
                if token:
                    logger.debug("Token loaded from system keyring")
                    return _sanitize_token(token)
            except Exception as e:
                logger.warning("keyring load failed: %s", e)

        # 2. Fernet (миграция со старой версии)
        if _FERNET_AVAILABLE and os.path.exists(_FERNET_FILE):
            try:
                with open(_FERNET_FILE, "rb") as f:
                    data = f.read()
                token = Fernet(_fernet_key()).decrypt(data).decode("utf-8")
                token = _sanitize_token(token)
                logger.debug("Token loaded from Fernet file — migrating to keyring")
                # Автомиграция: переносим в keyring и удаляем файл
                if _KEYRING_AVAILABLE:
                    TokenManager.save_token(token)
                return token
            except InvalidToken:
                logger.warning("Fernet token corrupted (wrong machine?) — deleting")
                TokenManager._remove_fernet_file()
            except Exception as e:
                logger.warning("Fernet load failed: %s", e)

        return None

    # ── Удаление ──────────────────────────────────────────────────────────────

    @staticmethod
    def delete_token() -> bool:
        """Удаляет токен из всех хранилищ."""
        deleted = False

        if _KEYRING_AVAILABLE:
            try:
                keyring.delete_password(_KEYRING_SERVICE, _KEYRING_USERNAME)
                deleted = True
                logger.debug("Token deleted from system keyring")
            except keyring.errors.PasswordDeleteError:
                pass  # Уже не было — ок
            except Exception as e:
                logger.warning("keyring delete failed: %s", e)

        if TokenManager._remove_fernet_file():
            deleted = True

        return deleted

    # ── Информация ────────────────────────────────────────────────────────────

    @staticmethod
    def storage_info() -> dict:
        """
        Возвращает информацию о текущем хранилище для отображения в UI.
        {
          'backend': 'keyring' | 'fernet' | 'none',
          'backend_name': 'Windows Credential Manager' | ...,
          'has_token': bool,
          'masked': 'ghp_****XyZ' | None,
        }
        """
        backend = "none"
        backend_name = "Not available"
        has_token = False
        masked = None

        if _KEYRING_AVAILABLE:
            try:
                kr = keyring.get_keyring()
                kr_name = type(kr).__name__
                # Человекочитаемые названия бэкендов
                names = {
                    "WinVaultKeyring":      "Windows Credential Manager",
                    "Keyring":              "Windows Credential Manager",
                    "SecretServiceKeyring": "Linux SecretService (GNOME/KDE)",
                    "KWalletKeyring":       "Linux KWallet",
                    "Keychain":             "macOS Keychain",
                    "OSXKeychain":          "macOS Keychain",
                }
                backend_name = names.get(kr_name, f"System Keyring ({kr_name})")
                backend = "keyring"
                token = keyring.get_password(_KEYRING_SERVICE, _KEYRING_USERNAME)
                if token:
                    has_token = True
                    masked = _mask_token(token)
            except Exception:
                pass

        if backend == "none" and _FERNET_AVAILABLE and os.path.exists(_FERNET_FILE):
            backend = "fernet"
            backend_name = "Encrypted file (Fernet/AES-128)"
            try:
                token = Fernet(_fernet_key()).decrypt(open(_FERNET_FILE, "rb").read()).decode()
                has_token = True
                masked = _mask_token(token)
            except Exception:
                pass

        return {
            "backend":      backend,
            "backend_name": backend_name,
            "has_token":    has_token,
            "masked":       masked,
        }

    @staticmethod
    def mask_url(url: str) -> str:
        """
        Маскирует токен в URL перед выводом в лог.
        https://ghp_AbCd@github.com/... → https://****@github.com/...
        """
        import re
        return re.sub(r'(https?://)([^@]+)(@)', r'\1****\3', url)

    # ── Приватное ─────────────────────────────────────────────────────────────

    @staticmethod
    def _remove_fernet_file() -> bool:
        if os.path.exists(_FERNET_FILE):
            try:
                os.remove(_FERNET_FILE)
                return True
            except Exception:
                pass
        return False
