# ui/main_window.py
import os
import webbrowser
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QTabWidget, QStatusBar, QProgressBar, QMessageBox, QLabel,
    QStyleFactory
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPalette, QColor, QFont

from config import COLORS, STYLESHEET
from utils.lang_manager import LanguageManager
from utils.repo_manager import RepositoryManager
from utils.git_helper import GitHelper
from utils.history import CommitHistoryManager

from ui.deploy_thread import DeployThread
from ui.deploy_tab import DeployTabMixin
from ui.branches_tab import BranchesTabMixin
from ui.gitignore_tab import GitignoreTabMixin
from ui.settings_tab import SettingsTabMixin
from ui.about_tab import AboutTabMixin
from ui.toolbar import ToolbarMixin
from ui.menu import MenuMixin
from ui.helpers import HelpersMixin
from ui.batch_tab import BatchTabMixin
from ui.graph_tab import GraphTabMixin

lang_mgr = LanguageManager()


class GitHubDeployerApp(
    QMainWindow,
    DeployTabMixin,
    BranchesTabMixin,
    GitignoreTabMixin,
    SettingsTabMixin,
    AboutTabMixin,
    ToolbarMixin,
    MenuMixin,
    HelpersMixin,
    BatchTabMixin,
    GraphTabMixin
):
    def __init__(self):
        super().__init__()
        self._apply_language()
        self.setGeometry(100, 100, 1100, 800)
        self.setMinimumSize(900, 650)

        self.default_path = os.getcwd()
        self.default_repo = "https://github.com/lukomsky85/app-up360.git"
        self.commit_history = CommitHistoryManager.load_history()
        self.repo_mgr = RepositoryManager()

        self._setup_styles()
        self._setup_menu()
        self._setup_ui()
        self._setup_toolbar()
        self._setup_statusbar()

        self._load_saved_token()
        self._update_token_status()

        if not GitHelper.is_git_installed():
            QMessageBox.critical(self, lang_mgr.get_text("errors.git_not_installed"),
                                 lang_mgr.get_text("messages.git_not_found"))

    def _apply_language(self):
        self.setWindowTitle(lang_mgr.get_text("app_title"))

    def _setup_styles(self):
        self.setStyle(QStyleFactory.create('Fusion'))
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(COLORS['bg']))
        palette.setColor(QPalette.WindowText, QColor(COLORS['text']))
        palette.setColor(QPalette.Base, QColor('#ffffff'))
        palette.setColor(QPalette.AlternateBase, QColor(COLORS['bg_secondary']))
        palette.setColor(QPalette.Button, QColor(COLORS['button_bg']))
        palette.setColor(QPalette.Highlight, QColor(COLORS['accent']))
        palette.setColor(QPalette.HighlightedText, QColor('#ffffff'))
        palette.setColor(QPalette.PlaceholderText, QColor(COLORS['text_muted']))
        self.setPalette(palette)
        self.setStyleSheet(STYLESHEET)

    # Порядок вкладок — единственное место, которое нужно менять
    TAB_DEFS = [
        ('deploy',       '_create_deploy_tab',    'tabs.deploy'),
        ('branches',     '_create_branches_tab',  'tabs.branches'),
        ('gitignore',    '_create_gitignore_tab', None),           # None = фиксированный заголовок
        ('settings',     '_create_settings_tab',  'tabs.settings'),
        ('graph',        '_create_graph_tab',      'tabs.graph'),
        ('batch_deploy', '_create_batch_tab',      'tabs.batch_deploy'),
        ('about',        '_create_about_tab',      'tabs.about'),
    ]

    TAB_FIXED_TITLES = {
        'gitignore': '  .gitignore  ',
    }

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_lay = QVBoxLayout(central)
        main_lay.setContentsMargins(10, 8, 10, 8)
        main_lay.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(False)
        main_lay.addWidget(self.tabs)

        self._build_tabs()

    def _build_tabs(self):
        """Создаёт все вкладки. Используется при старте и при смене языка."""
        for key, creator, text_key in self.TAB_DEFS:
            widget = getattr(self, creator)()
            title  = self.TAB_FIXED_TITLES.get(key) or ("  " + lang_mgr.get_text(text_key) + "  ")
            self.tabs.addTab(widget, title)

    def _retranslate_tabs(self, current_index):
        """Пересоздаёт вкладки с новым языком, восстанавливает данные и позицию."""
        # Сохраняем данные перед удалением виджетов
        saved = self._collect_ui_state()
        saved['tab_index'] = current_index

        # Удаляем старые вкладки
        while self.tabs.count():
            self.tabs.removeTab(0)

        # Пересоздаём
        self._build_tabs()

        # Восстанавливаем
        self._restore_ui_state(saved)

    def _collect_ui_state(self):
        """Собирает текущее состояние полей ввода."""
        return {
            'path':   self.path_input.text()        if hasattr(self, 'path_input')    else self.default_path,
            'repo':   self.repo_url.text()          if hasattr(self, 'repo_url')      else self.default_repo,
            'token':  self.token_input.text()       if hasattr(self, 'token_input')   else '',
            'branch': self.branch_combo.currentText() if hasattr(self, 'branch_combo') else 'main',
            'commit': self.commit_combo.currentText() if hasattr(self, 'commit_combo') else '',
            'graph_path': self._graph_path_input.text() if hasattr(self, '_graph_path_input') else '',
        }

    def _restore_ui_state(self, saved):
        """Восстанавливает поля ввода после пересоздания вкладок."""
        if hasattr(self, 'path_input')    and saved.get('path'):
            self.path_input.setText(saved['path'])
        if hasattr(self, 'repo_url')      and saved.get('repo'):
            self.repo_url.setText(saved['repo'])
        if hasattr(self, 'token_input')   and saved.get('token'):
            self.token_input.setText(saved['token'])
        if hasattr(self, 'branch_combo')  and saved.get('branch'):
            self.branch_combo.setCurrentText(saved['branch'])
        if hasattr(self, 'commit_combo')  and saved.get('commit'):
            self.commit_combo.setCurrentText(saved['commit'])
        if hasattr(self, '_graph_path_input') and saved.get('graph_path'):
            self._graph_path_input.setText(saved['graph_path'])
        if hasattr(self, '_batch_token') and hasattr(self, 'token_input'):
            self._batch_token.setText(saved.get('token', ''))

        idx = saved.get('tab_index', 0)
        if 0 <= idx < self.tabs.count():
            self.tabs.setCurrentIndex(idx)

        self._update_token_status()

    def _setup_statusbar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        self.status_label = QLabel(lang_mgr.get_text("status.ready"))
        self.statusbar.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(180)
        self.progress_bar.setMaximumHeight(12)
        self.progress_bar.setVisible(False)
        self.statusbar.addPermanentWidget(self.progress_bar)

    def start_deployment(self):
        path = self.path_input.text().strip()
        repo = self.repo_url.text().strip()
        token = self.token_input.text().strip()
        msg = self.commit_combo.currentText().strip()
        do_gitignore = self.gitignore_check.isChecked()
        branch = self.branch_combo.currentText().strip()
        create_branch = self.create_branch_check.isChecked()

        if not os.path.isdir(path):
            self._show_error(lang_mgr.get_text("errors.folder_not_found"),
                             lang_mgr.get_text("messages.folder_not_found").format(path))
            return

        if not repo or repo == "https://github.com/username/repository.git":
            reply = QMessageBox.question(self, lang_mgr.get_text("buttons.ok"),
                                         "Repository URL not changed. Continue?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return

        if not branch:
            branch = "main"

        if self.save_token_check.isChecked() and token:
            from utils.crypto import TokenManager
            TokenManager.save_token(token)

        self.deploy_btn.setEnabled(False)
        self.status_label.setText(lang_mgr.get_text("status.deploying").format(branch))
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        self.deploy_thread = DeployThread(path, repo, token, msg, do_gitignore, branch, create_branch)
        self.deploy_thread.log_signal.connect(self._log)
        self.deploy_thread.finished_signal.connect(self._deployment_finished)
        self.deploy_thread.start()

    def _deployment_finished(self, success, message):
        self.progress_bar.setVisible(False)
        self.deploy_btn.setEnabled(True)

        if success:
            self.status_label.setText(lang_mgr.get_text("status.ready"))
            self._log(lang_mgr.get_text("messages.deploy_success_message").format(message), 'success')
            self._refresh_branches()
            reply = QMessageBox.question(self, lang_mgr.get_text("messages.success"),
                                         lang_mgr.get_text("messages.deploy_success_question").format(message),
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                clean_url = self.repo_url.text().strip().replace('.git', '')
                webbrowser.open(clean_url)
        else:
            self.status_label.setText(lang_mgr.get_text("status.failed"))
            self._show_error(lang_mgr.get_text("errors.deploy_failed"), message)

    def closeEvent(self, event):
        if self.save_token_check.isChecked() and self.token_input.text().strip():
            from utils.crypto import TokenManager
            TokenManager.save_token(self.token_input.text().strip())
        self._save_settings()
        event.accept()
