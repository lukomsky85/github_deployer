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
            
    def _clear_history(self):
        """Очистка истории коммитов и деплоев"""
        if not self.commit_history:
            QMessageBox.information(
                self,
                lang_mgr.get_text("messages.info"),
                "История уже пуста"
            )
            return
        
        reply = QMessageBox.question(
            self,
            "Очистка истории",
            "Вы уверены, что хотите очистить всю историю коммитов?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.commit_history = []
            CommitHistoryManager.save_history(self.commit_history)
            
            if hasattr(self, 'commit_combo'):
                self.commit_combo.clear()
                self.commit_combo.addItem("")
            
            self.status_label.setText("История очищена")
            
            QMessageBox.information(
                self,
                lang_mgr.get_text("messages.success"),
                "История успешно очищена"
            )

    def _export_history(self):
        """Экспорт истории коммитов в файл"""
        from PyQt5.QtWidgets import QFileDialog
        import json
        from datetime import datetime
        
        if not self.commit_history:
            QMessageBox.warning(
                self,
                "Экспорт истории",
                "Нет истории для экспорта"
            )
            return
        
        # Диалог выбора файла
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить историю",
            f"deploy_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON files (*.json);;All files (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.commit_history, f, ensure_ascii=False, indent=2)
                
                QMessageBox.information(
                    self,
                    "Экспорт завершён",
                    f"История успешно экспортирована в:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Ошибка экспорта",
                    f"Не удалось экспортировать историю:\n{str(e)}"
                )
    
    def _import_history(self):
        """Импорт истории коммитов из файла"""
        from PyQt5.QtWidgets import QFileDialog
        import json
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Загрузить историю",
            "",
            "JSON files (*.json);;All files (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_history = json.load(f)
                
                if not isinstance(imported_history, list):
                    raise ValueError("Файл должен содержать список коммитов")
                
                reply = QMessageBox.question(
                    self,
                    "Импорт истории",
                    f"Найдено {len(imported_history)} записей.\n"
                    f"Заменить текущую историю (будет потеряна) или добавить?\n\n"
                    f"Нажмите Yes - заменить\n"
                    f"Нажмите No - добавить",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
                )
                
                if reply == QMessageBox.Yes:
                    self.commit_history = imported_history
                elif reply == QMessageBox.No:
                    self.commit_history.extend(imported_history)
                else:
                    return
                
                CommitHistoryManager.save_history(self.commit_history)
                
                # Обновляем комбобокс с коммитами
                if hasattr(self, 'commit_combo'):
                    self.commit_combo.clear()
                    self.commit_combo.addItem("")
                    # Можно добавить последние коммиты в комбобокс
                    for commit in self.commit_history[-10:]:  # последние 10
                        if isinstance(commit, dict) and 'message' in commit:
                            self.commit_combo.addItem(commit['message'])
                
                QMessageBox.information(
                    self,
                    "Импорт завершён",
                    f"История успешно импортирована. Всего записей: {len(self.commit_history)}"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Ошибка импорта",
                    f"Не удалось импортировать историю:\n{str(e)}"
                )

    def _reset_settings(self):
        """Сброс всех настроек приложения к значениям по умолчанию"""
        reply = QMessageBox.question(
            self,
            "Сброс настроек",
            "Вы уверены, что хотите сбросить все настройки к значениям по умолчанию?\n\n"
            "Будут удалены:\n"
            "- Сохранённый токен\n"
            "- История коммитов\n"
            "- Путь к проекту\n"
            "- URL репозитория\n"
            "- Настройки языка",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.commit_history = []
            CommitHistoryManager.save_history(self.commit_history)
            
            from utils.crypto import TokenManager
            TokenManager.save_token("")
            
            if hasattr(self, 'path_input'):
                self.path_input.setText("")
            if hasattr(self, 'repo_url'):
                self.repo_url.setText("https://github.com/username/repository.git")
            if hasattr(self, 'token_input'):
                self.token_input.setText("")
            if hasattr(self, 'branch_combo'):
                self.branch_combo.setCurrentText("main")
            if hasattr(self, 'commit_combo'):
                self.commit_combo.clear()
                self.commit_combo.addItem("")
            
            if lang_mgr.current_lang != 'ru':
                lang_mgr.set_language('ru')
                self._rebuild_menu()
                self._retranslate_tabs(self.tabs.currentIndex())
            
            self._update_token_status()
            self._save_app_state()
            
            self.status_label.setText("Настройки сброшены к значениям по умолчанию")
            
            QMessageBox.information(
                self,
                lang_mgr.get_text("messages.success"),
                "Все настройки успешно сброшены"
            )

    def _show_help(self):
        """Показывает справку по использованию программы"""
        help_text = """
        <h3>GitHub Deployer - Руководство по использованию</h3>
        
        <b>Основные возможности:</b><br>
        • Деплой проектов на GitHub<br>
        • Управление ветками (создание, переключение, удаление, слияние)<br>
        • Работа с .gitignore<br>
        • Граф коммитов<br>
        • Пакетный деплой<br>
        • Автоматизация задач<br><br>
        
        <b>Как начать:</b><br>
        1. Укажите путь к вашему проекту<br>
        2. Введите URL репозитория GitHub<br>
        3. Добавьте GitHub токен (Settings → Manage Token)<br>
        4. Выберите ветку и нажмите "Deploy"<br><br>
        
        <b>Горячие клавиши:</b><br>
        • Ctrl+O - Выбрать папку проекта<br>
        • F5 - Запустить деплой<br>
        • Ctrl+Q - Выйти из программы<br>
        """
        
        QMessageBox.about(self, "Справка", help_text)

    def _show_about(self):
        """Показывает информацию о программе"""
        about_text = """
        <h3>GitHub Deployer</h3>
        <b>Версия:</b> 1.1.0<br>
        <b>Автор:</b> GitHub Deployer Team<br>
        <b>Лицензия:</b> MIT<br><br>
        
        Программа для удобного деплоя проектов на GitHub<br>
        с поддержкой множества дополнительных функций.<br><br>
        
        <b>Особенности:</b><br>
        • Поддержка токенов GitHub<br>
        • Управление ветками<br>
        • Многоязычный интерфейс (Русский/English)<br>
        • Автоматическая обработка .gitignore<br>
        """
        
        QMessageBox.about(self, "О программе", about_text)

    def _manage_token(self):
        """Управление GitHub токеном"""
        settings_index = self._tab_index_by_key('settings')
        self.tabs.setCurrentIndex(settings_index)
        
        if hasattr(self, '_show_token_dialog'):
            self._show_token_dialog()
        else:
            from utils.crypto import TokenManager
            from PyQt5.QtWidgets import QInputDialog, QLineEdit
            
            current_token = TokenManager.load_token()
            token, ok = QInputDialog.getText(
                self,
                "GitHub Токен",
                "Введите ваш GitHub токен:",
                QLineEdit.Password,
                current_token
            )
            
            if ok and token:
                TokenManager.save_token(token)
                if hasattr(self, 'token_input'):
                    self.token_input.setText(token)
                self._update_token_status()
                QMessageBox.information(self, "Успех", "Токен успешно сохранён")
            elif ok and not token:
                TokenManager.save_token("")
                if hasattr(self, 'token_input'):
                    self.token_input.setText("")
                self._update_token_status()
                QMessageBox.information(self, "Токен удалён", "Токен был удалён")
                
    def _delete_token(self):
        """Удаление сохранённого GitHub токена"""
        from utils.crypto import TokenManager
        
        # Проверяем, есть ли сохранённый токен
        current_token = TokenManager.load_token()
        if not current_token:
            QMessageBox.information(
                self,
                "Удаление токена",
                "Нет сохранённого токена для удаления"
            )
            return
        
        reply = QMessageBox.question(
            self,
            "Удаление токена",
            "Вы уверены, что хотите удалить сохранённый GitHub токен?\n\n"
            "После удаления вам нужно будет вводить токен заново для деплоя.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            TokenManager.save_token("")
            if hasattr(self, 'token_input'):
                self.token_input.setText("")
            self._update_token_status()
            self.status_label.setText("Токен удалён")
            
            QMessageBox.information(
                self,
                "Токен удалён",
                "GitHub токен успешно удалён из хранилища"
            )
            
    def _check_token(self):
        """Проверка валидности GitHub токена"""
        from utils.crypto import TokenManager
        import requests
        
        token = TokenManager.load_token()
        if not token:
            # Если сохранённого нет, проверяем поле ввода
            if hasattr(self, 'token_input'):
                token = self.token_input.text().strip()
            if not token:
                QMessageBox.warning(
                    self,
                    "Проверка токена",
                    "Токен не найден. Пожалуйста, введите токен сначала."
                )
                return
        
        # Проверяем токен через GitHub API
        self.status_label.setText("Проверка токена...")
        QApplication.processEvents()
        
        try:
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            response = requests.get(
                "https://api.github.com/user",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                username = user_data.get('login', 'Неизвестно')
                
                # Проверяем права токена
                scopes = response.headers.get('X-OAuth-Scopes', 'не указаны')
                
                QMessageBox.information(
                    self,
                    "Токен валиден",
                    f"✅ Токен действителен!\n\n"
                    f"Пользователь: {username}\n"
                    f"Права: {scopes}\n\n"
                    f"Токен имеет доступ к репозиториям."
                )
                self.status_label.setText(f"Токен валиден (пользователь: {username})")
            elif response.status_code == 401:
                QMessageBox.critical(
                    self,
                    "Токен невалиден",
                    "❌ Токен недействителен или истёк.\n\n"
                    "Пожалуйста, проверьте токен и введите заново."
                )
                self.status_label.setText("Токен невалиден")
            else:
                QMessageBox.warning(
                    self,
                    "Ошибка проверки",
                    f"Не удалось проверить токен.\n"
                    f"Код ошибки: {response.status_code}\n"
                    f"Ответ: {response.text[:200]}"
                )
                self.status_label.setText("Ошибка проверки токена")
        except requests.exceptions.Timeout:
            QMessageBox.warning(
                self,
                "Таймаут",
                "Превышено время ожидания ответа от GitHub.\n"
                "Проверьте интернет-соединение."
            )
            self.status_label.setText("Таймаут при проверке токена")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Произошла ошибка при проверке токена:\n{str(e)}"
            )
            self.status_label.setText("Ошибка проверки токена")
       
            
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