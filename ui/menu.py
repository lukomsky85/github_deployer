# ui/menu.py
from PyQt5.QtWidgets import QAction
from PyQt5.QtCore import QSize
from utils.lang_manager import lang_mgr
from utils.icon_manager import IconManager


class MenuMixin:

    def _setup_menu(self):
        self._rebuild_menu()

    def _rebuild_menu(self):
        """Строит меню с нуля. Вызывается при старте и при смене языка."""
        self._icons = IconManager()
        menubar = self.menuBar()
        menubar.clear()

        def _act(text_key, icon_name=None, shortcut=None):
            # Убираем эмодзи из текста пункта меню — они не нужны
            # т.к. у нас есть SVG-иконки
            text = lang_mgr.get_text(text_key)
            text = _strip_emoji(text)
            a = QAction(text, self)
            if icon_name:
                self._icons.set_action_icon(a, icon_name, size=QSize(16, 16))
            if shortcut:
                a.setShortcut(shortcut)
            return a

        # ── File ─────────────────────────────────────────────────────────
        file_label = _strip_emoji(lang_mgr.get_text("menu.file"))
        file_menu = menubar.addMenu(file_label)

        a = _act("menu.select_project", "folder", "Ctrl+O")
        a.triggered.connect(lambda: self._browse_folder(self.path_input))
        file_menu.addAction(a)

        a = _act("menu.deploy", "deploy", "F5")
        a.triggered.connect(self.start_deployment)
        file_menu.addAction(a)

        file_menu.addSeparator()

        lang_menu = file_menu.addMenu(lang_mgr.get_text("menu.language"))
        for code in lang_mgr.get_available_languages():
            name = "Русский" if code == 'ru' else "English"
            la = QAction(name, self)
            la.setCheckable(True)
            la.setChecked(lang_mgr.current_lang == code)
            la.triggered.connect(lambda checked, c=code: self._change_language(c))
            lang_menu.addAction(la)

        file_menu.addSeparator()

        a = _act("menu.exit", shortcut="Ctrl+Q")
        a.triggered.connect(self.close)
        file_menu.addAction(a)

        # ── Branches ─────────────────────────────────────────────────────
        branch_label = _strip_emoji(lang_mgr.get_text("menu.branches"))
        branch_menu = menubar.addMenu(branch_label)

        for text_key, action_name, icon_name in [
            ("menu.create_branch", "create", "add"),
            ("menu.switch_branch", "switch", "refresh"),
            ("menu.delete_branch", "delete", "delete"),
        ]:
            a = _act(text_key, icon_name)
            a.triggered.connect(lambda checked, n=action_name: self._handle_branch_action(n))
            branch_menu.addAction(a)

        branch_menu.addSeparator()
        a = _act("menu.merge_branches", "branch")
        a.triggered.connect(lambda: self._handle_branch_action('merge'))
        branch_menu.addAction(a)

        # ── Settings ─────────────────────────────────────────────────────
        settings_label = _strip_emoji(lang_mgr.get_text("menu.settings"))
        settings_menu = menubar.addMenu(settings_label)

        a = _act("menu.manage_token", "token")
        a.triggered.connect(self._manage_token)
        settings_menu.addAction(a)

        a = _act("menu.clear_history", "clear")
        a.triggered.connect(self._clear_history)
        settings_menu.addAction(a)

        a = _act("menu.reset_settings", "settings")
        a.triggered.connect(self._reset_settings)
        settings_menu.addAction(a)

        # ── Help ─────────────────────────────────────────────────────────
        help_label = _strip_emoji(lang_mgr.get_text("menu.help"))
        help_menu = menubar.addMenu(help_label)

        a = _act("menu.help", "about", "F1")
        a.triggered.connect(self._show_help)
        help_menu.addAction(a)

        a = _act("menu.about", "about")
        a.triggered.connect(self._show_about)
        help_menu.addAction(a)

    def _change_language(self, code):
        if lang_mgr.current_lang == code:
            return
        if not lang_mgr.set_language(code):
            return

        current_tab = self.tabs.currentIndex()

        # 1. Меню
        self._apply_language()
        self._rebuild_menu()

        # 2. Тулбар (тултипы)
        self._retranslate_toolbar()

        # 3. Статусбар
        if hasattr(self, 'status_label'):
            self.status_label.setText(lang_mgr.get_text("status.ready"))

        # 4. Все вкладки
        self._retranslate_tabs(current_tab)

        # 5. Токен-статус
        self._update_token_status()


def _strip_emoji(text: str) -> str:
    """Убирает эмодзи и лишние пробелы из строки для меню."""
    import re
    # Удаляем символы эмодзи (Unicode ranges)
    text = re.sub(
        r'[\U0001F000-\U0001FFFF'
        r'\U00002600-\U000027FF'
        r'\U0000FE00-\U0000FEFF'
        r'\u2600-\u27FF'
        r'\U0001F300-\U0001F9FF'
        r']+',
        '', text
    )
    return text.strip()
