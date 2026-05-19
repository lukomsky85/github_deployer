# utils/lang_manager.py
import os
import json


class LanguageManager:
    """
    Глобальный синглтон для управления языком.
    Язык сохраняется в settings.json и загружается при старте.
    """
    _SETTINGS_FILE = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'settings.json'
    )

    def __init__(self):
        self.current_lang = 'en'   # fallback
        self.translations = {}
        # Загружаем сохранённый язык, иначе English
        saved = self._load_saved_lang()
        self._load_language(saved or 'en')

    def _get_lang_path(self, lang_code):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, 'languages', f'{lang_code}.json')

    def _load_language(self, lang_code):
        path = self._get_lang_path(lang_code)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
                self.current_lang = lang_code
                return True
        except Exception as e:
            print(f"[lang_manager] Failed to load '{lang_code}': {e}")
            return False

    def set_language(self, lang_code):
        """Сменить язык и сохранить выбор."""
        if self._load_language(lang_code):
            self._save_lang(lang_code)
            return True
        return False

    def get_text(self, key, **kwargs):
        """Получить перевод по точечному ключу: 'menu.file' -> translations['menu']['file']."""
        keys = key.split('.')
        value = self.translations
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, key)
            else:
                return key   # ключ не найден — возвращаем сам ключ как заглушку
        if isinstance(value, str) and kwargs:
            try:
                return value.format(**kwargs)
            except Exception:
                pass
        return value if isinstance(value, str) else key

    def get_available_languages(self):
        return ['en', 'ru']

    # ── Persist ──────────────────────────────────────────────────────────────

    def _load_saved_lang(self):
        """Читает сохранённый язык из settings.json."""
        try:
            with open(self._SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('language')
        except Exception:
            return None

    def _save_lang(self, lang_code):
        """Сохраняет язык в settings.json (мёрджит с существующими настройками)."""
        data = {}
        try:
            with open(self._SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            pass
        data['language'] = lang_code
        try:
            with open(self._SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[lang_manager] Failed to save language: {e}")


# ── Глобальный синглтон ───────────────────────────────────────────────────────
# Все модули импортируют именно этот объект — он один на всё приложение.
lang_mgr = LanguageManager()
