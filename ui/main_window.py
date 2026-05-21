# ui/main_window.py
import os
import webbrowser
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QTabWidget, QStatusBar, QProgressBar, QMessageBox, QLabel,
    QStyleFactory, QFileDialog, QPushButton, QComboBox,
    QCheckBox, QTextEdit, QGroupBox, QFormLayout, QHBoxLayout, QLineEdit
)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QPalette, QColor, QFont

from config import COLORS, STYLESHEET
from utils.lang_manager import lang_mgr
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
from ui.automation_tab import AutomationTabMixin


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
    GraphTabMixin,
    AutomationTabMixin  # ← Добавлен миксин для вкладки Автоматизация
):
    def __init__(self):
        super().__init__()
        self._apply_language()
        self.setGeometry(100, 100, 1100, 800)
        self.setMinimumSize(900, 650)

        self.default_path = os.getcwd()
        self.default_repo = "https://github.com/username/repository.git"
        self.commit_history = CommitHistoryManager.load_history()
        self.repo_mgr = RepositoryManager()

        self._setup_styles()
        self._setup_menu()
        self._setup_ui()
        self._setup_toolbar()
        self._setup_statusbar()

        self._load_app_state()
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
    # (key, creator_method, text_key_or_None, icon_name)
    TAB_DEFS = [
        ('deploy',       '_create_deploy_tab',    'tabs.deploy',        'deploy'),
        ('branches',     '_create_branches_tab',  'tabs.branches',      'branch'),
        ('gitignore',    '_create_gitignore_tab', None,                 'folder'),
        ('settings',     '_create_settings_tab',  'tabs.settings',      'settings'),
        ('graph',        '_create_graph_tab',      'tabs.graph',         'branch'),
        ('batch_deploy', '_create_batch_tab',      'tabs.batch_deploy',  'push'),
        ('automation',   '_create_automation_tab', 'tabs.automation',    'automation'),
        ('about',        '_create_about_tab',      'tabs.about',         'about'),
    ]

    TAB_FIXED_TITLES = {
        'gitignore': '.gitignore',
    }

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_lay = QVBoxLayout(central)
        main_lay.setContentsMargins(10, 8, 10, 8)
        main_lay.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(False)
        self.tabs.setIconSize(QSize(16, 16))
        self.tabs.currentChanged.connect(self._on_tab_changed)
        main_lay.addWidget(self.tabs)

        self._build_tabs()

    def _build_tabs(self):
        """Создаёт все вкладки с иконками. Используется при старте и при смене языка."""
        from utils.icon_manager import IconManager
        icons = IconManager()
        for key, creator, text_key, icon_name in self.TAB_DEFS:
            widget = getattr(self, creator)()
            title  = self.TAB_FIXED_TITLES.get(key) or lang_mgr.get_text(text_key)
            self.tabs.addTab(widget, title)
            # Все иконки серые — _on_tab_changed сразу перекрасит активную в белую
            icon = icons.get(icon_name, color='#6c6f85', size=QSize(16, 16))
            if icon:
                self.tabs.setTabIcon(self.tabs.count() - 1, icon)
        # Применяем цвет активной вкладки сразу после построения
        self._on_tab_changed(self.tabs.currentIndex())

    def _on_tab_changed(self, index):
        """Меняет цвет иконок: белая на активной (синий фон), серые на остальных."""
        from utils.icon_manager import IconManager
        icons = IconManager()
        for i, (key, creator, text_key, icon_name) in enumerate(self.TAB_DEFS):
            if i == index:
                # Активная вкладка — синий фон, иконка белая
                color = '#ffffff'
            else:
                # Неактивная — светло-серый фон, иконка серая
                color = '#6c6f85'
            icon = icons.get(icon_name, color=color, size=QSize(16, 16))
            if icon:
                self.tabs.setTabIcon(i, icon)

    def _tab_index_by_key(self, key):
        """Возвращает индекс вкладки по ключу из TAB_DEFS."""
        for i, (k, *_) in enumerate(self.TAB_DEFS):
            if k == key:
                return i
        return 0

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

    # ── Метод создания вкладки "Автоматизация" ──────────────────────────────
    def _create_automation_tab(self):
        """Делегирует в AutomationTabMixin из automation_tab.py."""
        return AutomationTabMixin._create_automation_tab(self)

    def _timestamp(self):
        """Возвращает текущее время в формате ЧЧ:ММ:СС"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
    # ── Конец методов вкладки Автоматизация ──────────────────────

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

    def _deployment_finished(self, success, branch_or_err):
        self.progress_bar.setVisible(False)
        self.deploy_btn.setEnabled(True)

        if success:
            branch = branch_or_err
            self.status_label.setText(lang_mgr.get_text("status.ready"))
            self._refresh_branches()

            # Кастомный диалог с переведёнными кнопками
            dlg = QMessageBox(self)
            dlg.setWindowTitle(lang_mgr.get_text("messages.success"))
            dlg.setText(lang_mgr.get_text("messages.deploy_success_question").format(branch=branch))
            dlg.setIcon(QMessageBox.Question)
            btn_yes = dlg.addButton(lang_mgr.get_text("buttons.yes"), QMessageBox.YesRole)
            btn_no  = dlg.addButton(lang_mgr.get_text("buttons.no"),  QMessageBox.NoRole)
            dlg.setDefaultButton(btn_no)
            dlg.exec_()

            if dlg.clickedButton() == btn_yes:
                clean_url = self.repo_url.text().strip().replace('.git', '')
                webbrowser.open(clean_url)
        else:
            self.status_label.setText(lang_mgr.get_text("status.failed"))
            self._show_error(lang_mgr.get_text("errors.deploy_failed"), branch_or_err)

    def closeEvent(self, event):
        if hasattr(self, 'save_token_check') and self.save_token_check.isChecked():
            token = self.token_input.text().strip() if hasattr(self, 'token_input') else ''
            if token:
                from utils.crypto import TokenManager
                TokenManager.save_token(token)
        self._save_app_state()
        event.accept()

    def _save_app_state(self):
        """Сохраняет настройки приложения (язык, путь, репо) в settings.json."""
        import json
        settings_file = lang_mgr._SETTINGS_FILE
        data = {}
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            pass
        data['language']     = lang_mgr.current_lang
        data['default_path'] = self.path_input.text() if hasattr(self, 'path_input') else ''
        data['default_repo'] = self.repo_url.text()   if hasattr(self, 'repo_url')   else ''
        data['last_branch']  = self.branch_combo.currentText() if hasattr(self, 'branch_combo') else 'main'
        try:
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[main_window] Failed to save app state: {e}")

    def _load_app_state(self):
        """Загружает сохранённые настройки и применяет их к полям UI."""
        import json
        try:
            with open(lang_mgr._SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            return
        if data.get('default_path') and hasattr(self, 'path_input'):
            self.path_input.setText(data['default_path'])
            self.default_path = data['default_path']
        if data.get('default_repo') and hasattr(self, 'repo_url'):
            self.repo_url.setText(data['default_repo'])
        if data.get('last_branch') and hasattr(self, 'branch_combo'):
            self.branch_combo.setCurrentText(data['last_branch'])