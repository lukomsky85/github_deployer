# ui/menu.py
from PyQt5.QtWidgets import (
    QMenuBar, QMenu, QAction, QMessageBox
)

from utils.lang_manager import lang_mgr

class MenuMixin:
    """Mixin для методов меню"""
    
    def _setup_menu(self):
        menubar = self.menuBar()
        
        # ===== File Menu =====
        file_menu = menubar.addMenu(lang_mgr.get_text("menu.file"))
        
        act = QAction(lang_mgr.get_text("menu.select_project"), self)
        act.setShortcut("Ctrl+O")
        act.triggered.connect(lambda: self._browse_folder(self.path_input))
        file_menu.addAction(act)
        
        act = QAction(lang_mgr.get_text("menu.deploy"), self)
        act.setShortcut("F5")
        act.triggered.connect(self.start_deployment)
        file_menu.addAction(act)
        
        file_menu.addSeparator()
        
        # Language Submenu
        lang_menu = file_menu.addMenu("🌍 Language")
        for code in lang_mgr.get_available_languages():
            name = "Русский" if code == 'ru' else "English"
            act = QAction(name, self)
            act.triggered.connect(lambda checked, c=code: self._change_language(c))
            lang_menu.addAction(act)
            
        file_menu.addSeparator()
        
        act = QAction(lang_mgr.get_text("menu.exit"), self)
        act.setShortcut("Ctrl+Q")
        act.triggered.connect(self.close)
        file_menu.addAction(act)
        
        # ===== Branches Menu =====
        branch_menu = menubar.addMenu(lang_mgr.get_text("menu.branches"))
        
        act = QAction(lang_mgr.get_text("menu.create_branch"), self)
        act.triggered.connect(lambda: self._handle_branch_action('create'))
        branch_menu.addAction(act)
        
        act = QAction(lang_mgr.get_text("menu.switch_branch"), self)
        act.triggered.connect(lambda: self._handle_branch_action('switch'))
        branch_menu.addAction(act)
        
        act = QAction(lang_mgr.get_text("menu.delete_branch"), self)
        act.triggered.connect(lambda: self._handle_branch_action('delete'))
        branch_menu.addAction(act)
        
        branch_menu.addSeparator()
        
        act = QAction(lang_mgr.get_text("menu.merge_branches"), self)
        act.triggered.connect(lambda: self._handle_branch_action('merge'))
        branch_menu.addAction(act)
        
        # ===== Settings Menu =====
        settings_menu = menubar.addMenu(lang_mgr.get_text("menu.settings"))
        
        act = QAction(lang_mgr.get_text("menu.manage_token"), self)
        act.triggered.connect(self._manage_token)
        settings_menu.addAction(act)
        
        act = QAction(lang_mgr.get_text("menu.clear_history"), self)
        act.triggered.connect(self._clear_history)
        settings_menu.addAction(act)
        
        act = QAction(lang_mgr.get_text("menu.reset_settings"), self)
        act.triggered.connect(self._reset_settings)
        settings_menu.addAction(act)
        
        # ===== Help Menu =====
        help_menu = menubar.addMenu(lang_mgr.get_text("menu.help"))
        
        act = QAction(lang_mgr.get_text("menu.help"), self)
        act.setShortcut("F1")
        act.triggered.connect(self._show_help)
        help_menu.addAction(act)
        
        act = QAction(lang_mgr.get_text("menu.about"), self)
        act.triggered.connect(self._show_about)
        help_menu.addAction(act)

    def _change_language(self, code):
        """Смена языка с пересозданием интерфейса и сохранением введённых данных"""
        if not lang_mgr.set_language(code):
            return

        # 1. Сохраняем текущие значения полей
        saved = {
            'path': self.path_input.text() if hasattr(self, 'path_input') else self.default_path,
            'repo': self.repo_url.text() if hasattr(self, 'repo_url') else self.default_repo,
            'token': self.token_input.text() if hasattr(self, 'token_input') else "",
            'branch': self.branch_combo.currentText() if hasattr(self, 'branch_combo') else "main",
            'commit': self.commit_combo.currentText() if hasattr(self, 'commit_combo') else "",
            'tab_index': self.tabs.currentIndex()
        }

        # 2. Обновляем меню и заголовок
        self._apply_language()
        self.menuBar().clear()
        self._setup_menu()
        if hasattr(self, 'status_label'):
            self.status_label.setText(lang_mgr.get_text("status.ready"))

        # 3. Удаляем старые вкладки
        while self.tabs.count() > 0:
            self.tabs.removeTab(0)

        # 4. Создаём новые вкладки (все тексты уже на новом языке)
        from ui.deploy_tab import DeployTabMixin
        from ui.branches_tab import BranchesTabMixin
        from ui.gitignore_tab import GitignoreTabMixin
        from ui.settings_tab import SettingsTabMixin
        from ui.about_tab import AboutTabMixin
        
        self.tabs.addTab(self._create_deploy_tab(), lang_mgr.get_text("tabs.deploy"))
        self.tabs.addTab(self._create_branches_tab(), lang_mgr.get_text("tabs.branches"))
        self.tabs.addTab(self._create_gitignore_tab(), "📁 .gitignore")
        self.tabs.addTab(self._create_settings_tab(), lang_mgr.get_text("tabs.settings"))
        self.tabs.addTab(self._create_about_tab(), lang_mgr.get_text("tabs.about"))

        # 5. Восстанавливаем введённые данные
        self.path_input.setText(saved['path'])
        self.repo_url.setText(saved['repo'])
        self.token_input.setText(saved['token'])
        self.branch_combo.setCurrentText(saved['branch'])
        self.commit_combo.setCurrentText(saved['commit'])
        self.tabs.setCurrentIndex(saved['tab_index'])

        # 6. Обновляем статус токена
        self._update_token_status()

        QMessageBox.information(self, "Language", f"Language changed to {code}")