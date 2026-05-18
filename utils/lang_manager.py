# utils/lang_manager.py
import os
import json

class LanguageManager:
    """Менеджер локализации с загрузкой из внешних файлов и поддержкой вложенных ключей"""
    
    def __init__(self, lang_dir='languages', fallback_lang='en'):
        self.lang_dir = lang_dir
        self.fallback_lang = fallback_lang
        self.current_lang = fallback_lang
        self._translations = {}
        self._fallback = {}
        self.on_language_changed = None
        
        self._load_fallback()
        self.set_language(fallback_lang)
    
    def _load_fallback(self):
        """Загружает язык по умолчанию (для фолбэка)"""
        path = os.path.join(self.lang_dir, f"{self.fallback_lang}.json")
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self._fallback = json.load(f)
            except Exception:
                pass
    
    def set_language(self, lang_code):
        """Загружает переводы для указанного языка"""
        path = os.path.join(self.lang_dir, f"{lang_code}.json")
        
        if not os.path.exists(path):
            return False
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self._translations = json.load(f)
        except Exception:
            return False
        
        self.current_lang = lang_code
        
        if self.on_language_changed:
            self.on_language_changed()
        
        return True
    
    def _get_nested(self, data, key, default=None):
        """
        Получает значение из вложенного dict по ключу с точками.
        Пример: _get_nested(data, "menu.file") → data["menu"]["file"]
        """
        if not key:
            return default
        
        keys = key.split('.')
        value = data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_text(self, key, **kwargs):
        """
        Получает текст по ключу с поддержкой:
        - вложенных ключей: "menu.file" → data["menu"]["file"]
        - форматирования: .format(**kwargs)
        - фолбэка на английский, если ключ не найден
        """
        # Ищем в текущем языке
        text = self._get_nested(self._translations, key)
        
        # Если не нашли — берём из фолбэка
        if text is None:
            text = self._get_nested(self._fallback, key, f"[MISSING:{key}]")
        
        # Форматируем, если переданы аргументы
        if kwargs and isinstance(text, str):
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError, IndexError):
                pass  # Если форматирование не удалось — возвращаем как есть
        
        return text
    
    def get_available_languages(self):
        """Возвращает список доступных языков (коды)"""
        langs = []
        if os.path.exists(self.lang_dir):
            for f in os.listdir(self.lang_dir):
                if f.endswith('.json'):
                    langs.append(f.replace('.json', ''))
        return langs or [self.fallback_lang]


# Глобальный экземпляр для удобного импорта
lang_mgr = LanguageManager()