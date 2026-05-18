# ui/menu.py
from PyQt5.QtWidgets import QAction
from PyQt5.QtCore import QSize
from utils.lang_manager import lang_mgr
from utils.icon_manager import IconManager


class MenuMixin:

    def _setup_menu(self):
        self._icons = IconManager()
        menubar = self.menuBar()

        def _act(text_key, icon_name=None, shortcut=None):
            a = QAction(lang_mgr.get_text(text_key), self)
            if icon_name:
                self._icons.set_action_icon(a, icon_name, size=QSize(16, 16))
            if shortcut:
                a.setShortcut(shortcut)
            return a

        # File
        file_menu = menubar.addMenu(lang_mgr.get_text("menu.file"))

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
            la.triggered.connect(lambda checked, c=code: self._change_language(c))
            lang_menu.addAction(la)

        file_menu.addSeparator()

        a = _act("menu.exit", shortcut="Ctrl+Q")
        a.triggered.connect(self.close)
        file_menu.addAction(a)

        # Branches
        branch_menu = menubar.addMenu(lang_mgr.get_text("menu.branches"))
        for text_key, action_name in [
            ("menu.create_branch", "create"),
            ("menu.switch_branch", "switch"),
            ("menu.delete_branch", "delete"),
        ]:
            a = QAction(lang_mgr.get_text(text_key), self)
            a.triggered.connect(lambda checked, n=action_name: self._handle_branch_action(n))
            branch_menu.addAction(a)

        branch_menu.addSeparator()
        a = QAction(lang_mgr.get_text("menu.merge_branches"), self)
        a.triggered.connect(lambda: self._handle_branch_action('merge'))
        branch_menu.addAction(a)

        # Settings
        settings_menu = menubar.addMenu(lang_mgr.get_text("menu.settings"))

        a = QAction(lang_mgr.get_text("menu.manage_token"), self)
        a.triggered.connect(self._manage_token)
        settings_menu.addAction(a)

        a = QAction(lang_mgr.get_text("menu.clear_history"), self)
        a.triggered.connect(self._clear_history)
        settings_menu.addAction(a)

        a = QAction(lang_mgr.get_text("menu.reset_settings"), self)
        a.triggered.connect(self._reset_settings)
        settings_menu.addAction(a)

        # Help
        help_menu = menubar.addMenu(lang_mgr.get_text("menu.help"))

        a = QAction(lang_mgr.get_text("menu.help"), self)
        a.setShortcut("F1")
        a.triggered.connect(self._show_help)
        help_menu.addAction(a)

        a = QAction(lang_mgr.get_text("menu.about"), self)
        a.triggered.connect(self._show_about)
        help_menu.addAction(a)

    def _change_language(self, code):
        if lang_mgr.current_lang == code:
            return
        if not lang_mgr.set_language(code):
            return

        current_tab = self.tabs.currentIndex()

        # Перестраиваем меню
        self._apply_language()
        self.menuBar().clear()
        self._setup_menu()

        # Обновляем строку статуса
        if hasattr(self, 'status_label'):
            self.status_label.setText(lang_mgr.get_text("status.ready"))

        # Пересоздаём все вкладки (включая graph и batch) с сохранением данных
        self._retranslate_tabs(current_tab)

        # Обновляем тулбар
        if hasattr(self, 'token_status_label'):
            self._update_token_status()
