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
    HelpersMixin
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

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_lay = QVBoxLayout(central)
        main_lay.setContentsMargins(10, 8, 10, 8)
        main_lay.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(False)
        main_lay.addWidget(self.tabs)

        self.tabs.addTab(self._create_deploy_tab(),    "  " + lang_mgr.get_text("tabs.deploy") + "  ")
        self.tabs.addTab(self._create_branches_tab(),  "  " + lang_mgr.get_text("tabs.branches") + "  ")
        self.tabs.addTab(self._create_gitignore_tab(), "  .gitignore  ")
        self.tabs.addTab(self._create_settings_tab(),  "  " + lang_mgr.get_text("tabs.settings") + "  ")
        self.tabs.addTab(self._create_about_tab(),     "  " + lang_mgr.get_text("tabs.about") + "  ")

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
