# utils/lang_manager.py
import os
import json

class LanguageManager:
    def __init__(self):
        self.current_lang = 'ru'  # Язык по умолчанию
        self.translations = {}
        self._load_language(self.current_lang)
    
    def _get_lang_path(self, lang_code):
        # Путь к файлу языка относительно корня проекта
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
            print(f"Failed to load language {lang_code}: {e}")
            return False

    def set_language(self, lang_code):
        if self._load_language(lang_code):
            return True
        return False
    
    def get_text(self, key, **kwargs):
        """
        Получение текста по ключу с поддержкой вложенности.
        Ключи разделяются точкой: "menu.file" -> translations["menu"]["file"]
        """
        keys = key.split('.')
        value = self.translations
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, key)  # Возвращаем ключ если не нашли
            else:
                return key  # Не словарь — возвращаем ключ как заглушку
        
        # Форматирование строки если есть аргументы
        if isinstance(value, str) and kwargs:
            try:
                return value.format(**kwargs)
            except:
                pass  # Если форматирование не удалось — возвращаем как есть
        
        return value
    
    def get_available_languages(self):
        return ['en', 'ru']


# ============================================================================
# 🌍 GLOBAL INSTANCE
# ============================================================================

# Создаём глобальный экземпляр для импорта в других модулях
lang_mgr = LanguageManager()