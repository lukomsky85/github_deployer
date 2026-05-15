# utils/icon_manager.py
import os
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtCore import QSize, Qt, QByteArray


class IconManager:
    """
    Централизованный менеджер SVG-иконок.
    Поддерживает перекраску через цвет (белый для синих кнопок, тёмный для обычных).
    """

    _instance = None
    _cache = {}

    # Цвета по умолчанию
    COLOR_DARK    = "#4c4f69"   # иконки на светлых кнопках
    COLOR_MUTED   = "#6c6f85"   # иконки в toolbar/menu
    COLOR_WHITE   = "#ffffff"   # иконки на синих/тёмных кнопках
    COLOR_RED     = "#d20f39"   # иконки удаления
    COLOR_BLUE    = "#1e66f5"   # акцентные иконки
    COLOR_GREEN   = "#40a02b"   # иконки успеха
    COLOR_ORANGE  = "#df8e1d"   # иконки предупреждения

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.icons_dir = os.path.join(base_dir, 'icons')

    def _load_svg_bytes(self, name, category='actions'):
        """Загружает SVG-файл и возвращает его содержимое как bytes."""
        for ext in ('svg', 'png'):
            path = os.path.join(self.icons_dir, category, f"{name}.{ext}")
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    return f.read(), ext
        return None, None

    def get(self, name, color=None, size=None, category='actions'):
        """
        Получить QIcon с заданным цветом.

        Args:
            name:     имя иконки без расширения ('deploy', 'add', ...)
            color:    цвет строкой '#rrggbb' или None (используется COLOR_DARK)
            size:     QSize или None → 24×24
            category: подпапка в icons/
        Returns:
            QIcon или None
        """
        if color is None:
            color = self.COLOR_DARK
        if size is None:
            size = QSize(24, 24)

        cache_key = f"{category}/{name}/{color}/{size.width()}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        data, ext = self._load_svg_bytes(name, category)
        if data is None:
            return None

        if ext == 'svg':
            icon = self._colorize_svg(data, color, size)
        else:
            icon = QIcon(os.path.join(self.icons_dir, category, f"{name}.png"))

        self._cache[cache_key] = icon
        return icon

    def _colorize_svg(self, svg_bytes, color, size):
        """Рендерит SVG с заменой currentColor на нужный цвет → QIcon."""
        # Заменяем currentColor и явный чёрный на нужный цвет
        svg_str = svg_bytes.decode('utf-8', errors='replace')
        svg_str = svg_str.replace('currentColor', color)
        svg_str = svg_str.replace('stroke="#000000"', f'stroke="{color}"')
        svg_str = svg_str.replace('fill="#000000"', f'fill="{color}"')

        renderer = QSvgRenderer(QByteArray(svg_str.encode('utf-8')))
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return QIcon(pixmap)

    # ── Удобные методы для установки иконок ─────────────────────────────

    def set_button_icon(self, button, name, category='actions',
                        color=None, size=None):
        """
        Установить иконку на QPushButton.
        color=None → автоматически COLOR_DARK.
        """
        if size is None:
            size = QSize(16, 16)
        icon = self.get(name, color=color, size=size, category=category)
        if icon:
            button.setIcon(icon)
            button.setIconSize(size)
        return button

    def set_primary_button_icon(self, button, name, category='actions',
                                 size=None):
        """Иконка для синих (primary) кнопок — всегда белая."""
        if size is None:
            size = QSize(16, 16)
        icon = self.get(name, color=self.COLOR_WHITE, size=size, category=category)
        if icon:
            button.setIcon(icon)
            button.setIconSize(size)
        return button

    def set_danger_button_icon(self, button, name, category='actions',
                                size=None):
        """Иконка для кнопок удаления — красная."""
        if size is None:
            size = QSize(16, 16)
        icon = self.get(name, color=self.COLOR_RED, size=size, category=category)
        if icon:
            button.setIcon(icon)
            button.setIconSize(size)
        return button

    def set_action_icon(self, action, name, category='actions',
                        color=None, size=None):
        """Установить иконку на QAction (меню/тулбар)."""
        if size is None:
            size = QSize(20, 20)
        if color is None:
            color = self.COLOR_MUTED
        icon = self.get(name, color=color, size=size, category=category)
        if icon:
            action.setIcon(icon)
        return action

    def set_window_icon(self, window, name='logo', category='app'):
        """Иконка окна приложения."""
        icon = self.get(name, color=self.COLOR_BLUE,
                        size=QSize(32, 32), category=category)
        if icon:
            window.setWindowIcon(icon)

    def get_status_icon(self, level, size=None):
        """Иконка для уровня лога (success/warning/error/info)."""
        if size is None:
            size = QSize(14, 14)
        mapping = {
            'success': ('success', self.COLOR_GREEN),
            'warning': ('warning', self.COLOR_ORANGE),
            'error':   ('error',   self.COLOR_RED),
            'info':    ('info',    self.COLOR_BLUE),
        }
        name, color = mapping.get(level.lower(), ('info', self.COLOR_BLUE))
        return self.get(name, color=color, size=size, category='status')
