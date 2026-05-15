# utils/icon_manager.py
import os
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import QSize

class IconManager:
    """Централизованный менеджер иконок с кэшированием и фолбэками"""
    
    _instance = None
    _cache = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        # Путь к папке icons (относительно корня проекта)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.icons_dir = os.path.join(base_dir, 'icons')
        
        # Размеры иконок по умолчанию
        self.default_size = QSize(20, 20)
        self.toolbar_size = QSize(24, 24)
        self.button_size = QSize(16, 16)
        
        # Фолбэк-иконки (если кастомная не найдена)
        self.fallbacks = {
            'deploy': '🚀',
            'fetch': '📥',
            'push': '🚀',
            'commit': '💾',
            'refresh': '🔄',
            'folder': '📁',
            'token': '🔑',
            'add': '➕',
            'edit': '✏️',
            'delete': '🗑️',
            'save': '💾',
            'settings': '⚙️',
            'about': 'ℹ️',
            'success': '✅',
            'warning': '⚠️',
            'error': '❌',
            'info': 'ℹ️',
        }
    
    def get(self, name, size=None, category='actions'):
        """
        Получить иконку по имени.
        
        Args:
            name: Имя иконки (без расширения), например 'deploy'
            size: QSize или None (используется default_size)
            category: Папка в icons/, например 'actions', 'status', 'app'
        
        Returns:
            QIcon или строку-эмодзи как фолбэк
        """
        if size is None:
            size = self.default_size
            
        cache_key = f"{category}/{name}/{size.width()}x{size.height()}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Пробуем загрузить SVG
        svg_path = os.path.join(self.icons_dir, category, f"{name}.svg")
        if os.path.exists(svg_path):
            icon = QIcon(svg_path)
            self._cache[cache_key] = icon
            return icon
        
        # Пробуем PNG
        png_path = os.path.join(self.icons_dir, category, f"{name}.png")
        if os.path.exists(png_path):
            icon = QIcon(png_path)
            self._cache[cache_key] = icon
            return icon
        
        # Фолбэк: эмодзи или текст
        fallback = self.fallbacks.get(name, '•')
        self._cache[cache_key] = fallback
        return fallback
    
    def set_button_icon(self, button, name, category='actions', size=None):
        """Установить иконку на QPushButton"""
        icon = self.get(name, size, category)
        if isinstance(icon, QIcon):
            button.setIcon(icon)
            if size:
                button.setIconSize(size)
            else:
                button.setIconSize(self.button_size)
        else:
            # Фолбэк: текст вместо иконки
            button.setText(f"{icon} {button.text()}")
        return button
    
    def set_action_icon(self, action, name, category='actions', size=None):
        """Установить иконку на QAction"""
        icon = self.get(name, size, category)
        if isinstance(icon, QIcon):
            action.setIcon(icon)
        else:
            action.setText(f"{icon} {action.text()}")
        return action
    
    def set_window_icon(self, window, name='logo', category='app'):
        """Установить иконку окна приложения"""
        icon = self.get(name, category=category)
        if isinstance(icon, QIcon):
            window.setWindowIcon(icon)
    
    def get_status_icon(self, level):
        """Получить иконку для уровня сообщения (success/warning/error)"""
        mapping = {
            'success': ('success', 'status'),
            'warning': ('warning', 'status'),
            'error': ('error', 'status'),
            'info': ('info', 'status'),
        }
        name, category = mapping.get(level.lower(), ('info', 'status'))
        return self.get(name, category=category)