# ui/menu.py
from PyQt5.QtWidgets import QAction, QMessageBox
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
        if not lang_mgr.set_language(code):
            return
        saved = {
            'path':      self.path_input.text() if hasattr(self, 'path_input') else self.default_path,
            'repo':      self.repo_url.text() if hasattr(self, 'repo_url') else self.default_repo,
            'token':     self.token_input.text() if hasattr(self, 'token_input') else "",
            'branch':    self.branch_combo.currentText() if hasattr(self, 'branch_combo') else "main",
            'commit':    self.commit_combo.currentText() if hasattr(self, 'commit_combo') else "",
            'tab_index': self.tabs.currentIndex(),
        }
        self._apply_language()
        self.menuBar().clear()
        self._setup_menu()
        if hasattr(self, 'status_label'):
            self.status_label.setText(lang_mgr.get_text("status.ready"))

        while self.tabs.count() > 0:
            self.tabs.removeTab(0)

        self.tabs.addTab(self._create_deploy_tab(),    lang_mgr.get_text("tabs.deploy"))
        self.tabs.addTab(self._create_branches_tab(),  lang_mgr.get_text("tabs.branches"))
        self.tabs.addTab(self._create_gitignore_tab(), ".gitignore")
        self.tabs.addTab(self._create_settings_tab(),  lang_mgr.get_text("tabs.settings"))
        self.tabs.addTab(self._create_about_tab(),     lang_mgr.get_text("tabs.about"))

        self.path_input.setText(saved['path'])
        self.repo_url.setText(saved['repo'])
        self.token_input.setText(saved['token'])
        self.branch_combo.setCurrentText(saved['branch'])
        self.commit_combo.setCurrentText(saved['commit'])
        self.tabs.setCurrentIndex(saved['tab_index'])
        self._update_token_status()

        QMessageBox.information(self, "Language",
                                f"Language changed to {'Russian' if code == 'ru' else 'English'}")
