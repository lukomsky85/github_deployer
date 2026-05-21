# ui/deploy_tab.py
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QComboBox, QCheckBox, QGroupBox,
    QScrollArea, QFrame, QSizePolicy
)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QTimer, QSize

from config import DEFAULT_GITIGNORE
from utils.lang_manager import lang_mgr
from utils.repo_manager import RepositoryManager
from utils.icon_manager import IconManager  # ← Импорт менеджера иконок


class DeployTabMixin:
    """Mixin для методов вкладки Deploy"""

    def _create_deploy_tab(self):
        tab = QWidget()
        root_layout = QVBoxLayout(tab)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        root_layout.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # ── Инициализация менеджера иконок ─────────────────────────────
        self.icons = IconManager()

        # ── Repository Profile Selector ──────────────────────────────────
        profile_group = QGroupBox(lang_mgr.get_text("deploy_tab.repo_profiles_group"))
        pg_layout = QHBoxLayout(profile_group)
        pg_layout.setSpacing(6)

        self.repo_combo = QComboBox()
        self.repo_combo.setEditable(False)
        self.repo_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.repo_combo.currentIndexChanged.connect(self._on_repo_selected)
        pg_layout.addWidget(self.repo_combo)

        # Кнопка "Добавить" с иконкой
        btn_add = QPushButton(lang_mgr.get_text("buttons.add"))
        btn_add.setMinimumWidth(110)
        btn_add.setToolTip(lang_mgr.get_text("deploy_tab.add_profile_tooltip"))
        self.icons.set_button_icon(btn_add, 'add', size=QSize(16, 16))
        btn_add.clicked.connect(self._add_repo)
        pg_layout.addWidget(btn_add)

        # Кнопка "Изменить" с иконкой
        btn_edit = QPushButton(lang_mgr.get_text("buttons.edit"))
        btn_edit.setMinimumWidth(100)
        btn_edit.setToolTip(lang_mgr.get_text("deploy_tab.edit_profile_tooltip"))
        self.icons.set_button_icon(btn_edit, 'edit', size=QSize(16, 16))
        btn_edit.clicked.connect(self._edit_repo)
        pg_layout.addWidget(btn_edit)

        # Кнопка "Удалить" с иконкой
        btn_del = QPushButton(lang_mgr.get_text("buttons.delete"))
        btn_del.setMinimumWidth(100)
        btn_del.setToolTip(lang_mgr.get_text("deploy_tab.delete_profile_tooltip"))
        btn_del.setStyleSheet("QPushButton { color: #d20f39; } QPushButton:hover { color: #d20f39; border-color: #d20f39; }")
        self.icons.set_danger_button_icon(btn_del, 'delete', size=QSize(16, 16))
        btn_del.clicked.connect(self._delete_repo)
        pg_layout.addWidget(btn_del)

        # Кнопка "Сохранить профиль" с иконкой
        self.btn_save_profile = QPushButton(lang_mgr.get_text("deploy_tab.save_profile_button"))
        self.btn_save_profile.setMinimumWidth(160)
        self.btn_save_profile.setStyleSheet(
            "QPushButton { background-color: #e8f0fe; color: #1e66f5; border-color: #b8d0fb; }"
            "QPushButton:hover { background-color: #d0e4fd; }"
        )
        self.icons.set_button_icon(self.btn_save_profile, 'save', color='#1e66f5', size=QSize(16, 16))
        self.btn_save_profile.clicked.connect(self._save_current_profile)
        pg_layout.addWidget(self.btn_save_profile)

        layout.addWidget(profile_group)

        # ── Two-column row: Project + Repository ────────────────────────
        two_col = QHBoxLayout()
        two_col.setSpacing(10)

        # Project
        project_group = QGroupBox(lang_mgr.get_text("deploy_tab.project_group"))
        project_layout = QVBoxLayout(project_group)
        project_layout.setSpacing(6)

        path_row = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setText(self.default_path)
        self.path_input.setPlaceholderText(lang_mgr.get_text("deploy_tab.path_placeholder"))
        self.path_input.textChanged.connect(self._sync_paths)
        path_row.addWidget(self.path_input)

        # Кнопка "Обзор" с иконкой
        browse_btn = QPushButton()
        browse_btn.setFixedSize(36, 36)
        browse_btn.setToolTip(lang_mgr.get_text("deploy_tab.browse_button"))
        browse_btn.setStyleSheet("QPushButton { padding: 4px; }")
        self.icons.set_button_icon(browse_btn, 'folder', size=QSize(20, 20))
        browse_btn.clicked.connect(lambda: self._browse_folder(self.path_input))
        path_row.addWidget(browse_btn)
        project_layout.addLayout(path_row)

        quick_row = QHBoxLayout()
        quick_row.setSpacing(6)
        lbl_quick = QLabel(lang_mgr.get_text("deploy_tab.quick_access") + ":")
        lbl_quick.setStyleSheet("color: #8c8fa1; font-size: 9pt;")
        quick_row.addWidget(lbl_quick)
        
        cur_btn = QPushButton(lang_mgr.get_text("deploy_tab.current_folder"))
        cur_btn.setFixedHeight(28)
        cur_btn.setStyleSheet("QPushButton { font-size: 9pt; padding: 3px 10px; }")
        self.icons.set_button_icon(cur_btn, 'folder', size=QSize(14, 14))
        cur_btn.clicked.connect(lambda: self.path_input.setText(os.getcwd()))
        quick_row.addWidget(cur_btn)
        
        desk_btn = QPushButton(lang_mgr.get_text("deploy_tab.desktop"))
        desk_btn.setFixedHeight(28)
        desk_btn.setStyleSheet("QPushButton { font-size: 9pt; padding: 3px 10px; }")
        self.icons.set_button_icon(desk_btn, 'folder', size=QSize(14, 14))
        desk_btn.clicked.connect(lambda: self.path_input.setText(os.path.expanduser("~/Desktop")))
        quick_row.addWidget(desk_btn)
        
        quick_row.addStretch()
        project_layout.addLayout(quick_row)

        two_col.addWidget(project_group, 1)

        # Repository
        repo_group = QGroupBox(lang_mgr.get_text("deploy_tab.repository_group"))
        repo_layout = QVBoxLayout(repo_group)
        repo_layout.setSpacing(6)

        self.repo_url = QLineEdit()
        self.repo_url.setText(self.default_repo)
        self.repo_url.setPlaceholderText(lang_mgr.get_text("deploy_tab.repo_placeholder"))
        repo_layout.addWidget(self.repo_url)

        branch_row = QHBoxLayout()
        branch_row.setSpacing(6)
        branch_row.addWidget(QLabel(lang_mgr.get_text("deploy_tab.branch_label")))
        self.branch_combo = QComboBox()
        self.branch_combo.addItems(["main", "develop", "master"])
        self.branch_combo.setEditable(True)
        self.branch_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        branch_row.addWidget(self.branch_combo)
        
        # Кнопка "Обновить ветки" с иконкой
        refresh_btn = QPushButton()
        refresh_btn.setFixedSize(36, 36)
        refresh_btn.setToolTip(lang_mgr.get_text("deploy_tab.refresh_button"))
        refresh_btn.setStyleSheet("QPushButton { padding: 4px; }")
        self.icons.set_button_icon(refresh_btn, 'refresh', size=QSize(20, 20))
        refresh_btn.clicked.connect(self._refresh_branches)
        branch_row.addWidget(refresh_btn)
        repo_layout.addLayout(branch_row)

        two_col.addWidget(repo_group, 1)
        layout.addLayout(two_col)

        # ── Token ───────────────────────────────────────────────────────
        token_group = QGroupBox(lang_mgr.get_text("deploy_tab.token_group"))
        token_layout = QVBoxLayout(token_group)
        token_layout.setSpacing(6)

        token_row = QHBoxLayout()
        token_row.setSpacing(6)
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.Password)
        self.token_input.setPlaceholderText(lang_mgr.get_text("deploy_tab.token_placeholder"))
        self.token_input.textChanged.connect(self._update_token_status)
        token_row.addWidget(self.token_input)

        # Кнопка "Вставить" с иконкой
        paste_btn = QPushButton()
        paste_btn.setFixedSize(36, 36)
        paste_btn.setToolTip(lang_mgr.get_text("deploy_tab.paste_button"))
        paste_btn.setStyleSheet("QPushButton { padding: 4px; }")
        self.icons.set_button_icon(paste_btn, 'token', size=QSize(20, 20))
        paste_btn.clicked.connect(self._paste_token)
        token_row.addWidget(paste_btn)

        self.show_check = QCheckBox(lang_mgr.get_text("deploy_tab.show_checkbox"))
        self.show_check.toggled.connect(lambda c: self.token_input.setEchoMode(
            QLineEdit.Normal if c else QLineEdit.Password))
        token_row.addWidget(self.show_check)

        self.save_token_check = QCheckBox(lang_mgr.get_text("deploy_tab.save_checkbox"))
        self.save_token_check.setChecked(True)
        token_row.addWidget(self.save_token_check)

        token_layout.addLayout(token_row)

        token_info = QLabel(lang_mgr.get_text("deploy_tab.token_info"))
        token_info.setStyleSheet("color: #df8e1d; font-size: 8.5pt;")
        token_layout.addWidget(token_info)

        layout.addWidget(token_group)

        # ── Commit + Options (two-column) ────────────────────────────────
        two_col2 = QHBoxLayout()
        two_col2.setSpacing(10)

        commit_group = QGroupBox(lang_mgr.get_text("deploy_tab.commit_group"))
        commit_layout = QVBoxLayout(commit_group)
        commit_layout.setSpacing(6)
        commit_layout.addWidget(QLabel(lang_mgr.get_text("deploy_tab.commit_label")))
        commit_row = QHBoxLayout()
        self.commit_combo = QComboBox()
        self.commit_combo.setEditable(True)
        self.commit_combo.addItems(self.commit_history)
        self.commit_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        commit_row.addWidget(self.commit_combo)
        
        # Кнопка "Добавить коммит" с иконкой
        add_btn = QPushButton()
        add_btn.setFixedSize(36, 36)
        add_btn.setToolTip(lang_mgr.get_text("deploy_tab.add_commit_tooltip"))
        add_btn.setStyleSheet("QPushButton { padding: 4px; }")
        self.icons.set_button_icon(add_btn, 'add', size=QSize(20, 20))
        add_btn.clicked.connect(self._add_custom_commit)
        commit_row.addWidget(add_btn)
        commit_layout.addLayout(commit_row)
        two_col2.addWidget(commit_group, 2)

        options_group = QGroupBox(lang_mgr.get_text("deploy_tab.options_group"))
        options_layout = QVBoxLayout(options_group)
        options_layout.setSpacing(6)
        
        self.gitignore_check = QCheckBox(lang_mgr.get_text("deploy_tab.gitignore_check"))
        self.gitignore_check.setChecked(True)
        options_layout.addWidget(self.gitignore_check)
        
        self.create_branch_check = QCheckBox(lang_mgr.get_text("deploy_tab.create_branch_check"))
        self.create_branch_check.setChecked(False)
        options_layout.addWidget(self.create_branch_check)
        
        # Кнопка "Предпросмотр .gitignore" с иконкой
        preview_btn = QPushButton(" " + lang_mgr.get_text("deploy_tab.preview_button"))
        self.icons.set_button_icon(preview_btn, 'folder', size=QSize(16, 16))
        preview_btn.clicked.connect(self._preview_gitignore)
        options_layout.addWidget(preview_btn)
        two_col2.addWidget(options_group, 1)

        layout.addLayout(two_col2)

        # ── Log ─────────────────────────────────────────────────────────
        log_group = QGroupBox(lang_mgr.get_text("deploy_tab.log_group"))
        log_layout = QVBoxLayout(log_group)
        log_layout.setSpacing(6)

        log_btns = QHBoxLayout()
        
        # Кнопка "Очистить лог" с иконкой
        clear_btn = QPushButton(" " + lang_mgr.get_text("deploy_tab.clear_log_button"))
        clear_btn.setMinimumWidth(120)
        self.icons.set_danger_button_icon(clear_btn, 'clear', size=QSize(16, 16))
        clear_btn.clicked.connect(self._clear_log)
        log_btns.addWidget(clear_btn)
        
        # Кнопка "Сохранить лог" с иконкой
        save_log_btn = QPushButton(" " + lang_mgr.get_text("deploy_tab.save_log_button"))
        save_log_btn.setMinimumWidth(130)
        self.icons.set_button_icon(save_log_btn, 'save', size=QSize(16, 16))
        save_log_btn.clicked.connect(self._save_log)
        log_btns.addWidget(save_log_btn)
        
        log_btns.addStretch()
        log_layout.addLayout(log_btns)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Consolas", 9))
        self.log_output.setMinimumHeight(140)
        self.log_output.setStyleSheet(
            "QTextEdit { background-color: #f8f9fc; border: 1px solid #dce0e8; border-radius: 7px; padding: 6px; }"
        )
        log_layout.addWidget(self.log_output)
        layout.addWidget(log_group)

        # ── Deploy Button ────────────────────────────────────────────────
        deploy_row = QHBoxLayout()
        deploy_row.addStretch()
        
        # Главная кнопка деплоя с большой иконкой
        self.deploy_btn = QPushButton("  " + lang_mgr.get_text("deploy_tab.deploy_button") + "  ")
        self.deploy_btn.setMinimumHeight(44)
        self.deploy_btn.setMinimumWidth(180)
        self.deploy_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e66f5;
                color: white;
                font-size: 13px;
                font-weight: 600;
                border: none;
                border-radius: 9px;
                padding: 10px 32px;
            }
            QPushButton:hover { background-color: #1554d4; }
            QPushButton:pressed { background-color: #0e44b4; }
            QPushButton:disabled { background-color: #9bb8f5; color: #e0e8ff; }
        """)
        self.icons.set_primary_button_icon(self.deploy_btn, 'deploy', size=QSize(22, 22))
        self.deploy_btn.clicked.connect(self.start_deployment)
        deploy_row.addWidget(self.deploy_btn)
        deploy_row.addStretch()
        layout.addLayout(deploy_row)
        layout.addSpacing(6)

        QTimer.singleShot(100, self._refresh_repo_combo)
        return tab

    # ── Repository Profile Methods ───────────────────────────────────────

    def _refresh_repo_combo(self):
        if not hasattr(self, 'repo_mgr'):
            return
        current = self.repo_combo.currentText()
        self.repo_combo.clear()
        self.repo_combo.addItems(self.repo_mgr.get_all_names())
        if current in self.repo_mgr.get_all_names():
            self.repo_combo.setCurrentText(current)
        elif self.repo_combo.count() > 0:
            self.repo_combo.setCurrentIndex(0)
        self._on_repo_selected(self.repo_combo.currentIndex())

    def _on_repo_selected(self, index):
        if not hasattr(self, 'repo_mgr'):
            return
        repo = self.repo_mgr.get(index)
        if repo:
            self.path_input.setText(repo.get('path', ''))
            self.repo_url.setText(repo.get('url', ''))
            self.branch_combo.setCurrentText(repo.get('branch', 'main'))
            self.token_input.setText(repo.get('token', ''))
            self._update_token_status()

    def _add_repo(self):
        from ui.dialogs import RepoDialog
        dlg = RepoDialog(self)
        if dlg.exec_():
            data = dlg.get_data()
            if data['name'] and data['path']:
                self.repo_mgr.add(data)
                self._refresh_repo_combo()
                self._log(f"Added profile: {data['name']}", 'success')

    def _edit_repo(self):
        from ui.dialogs import RepoDialog
        idx = self.repo_combo.currentIndex()
        repo = self.repo_mgr.get(idx)
        if not repo:
            self._log("No profile selected", 'warning')
            return
        dlg = RepoDialog(self, repo)
        if dlg.exec_():
            data = dlg.get_data()
            if data['name'] and data['path']:
                self.repo_mgr.update(idx, data)
                self._refresh_repo_combo()
                self._log(f"Updated profile: {data['name']}", 'success')

    def _delete_repo(self):
        idx = self.repo_combo.currentIndex()
        if idx < 0:
            return
        repo = self.repo_mgr.get(idx)
        if repo and self._confirm(f"Delete profile '{repo['name']}'?"):
            self.repo_mgr.delete(idx)
            self._refresh_repo_combo()
            self._log(f"Deleted profile: {repo['name']}", 'warning')

    def _save_current_profile(self):
        idx = self.repo_combo.currentIndex()
        if idx < 0:
            self._log("Select a profile first", 'warning')
            return
        data = {
            'name': self.repo_mgr.get(idx)['name'],
            'path': self.path_input.text().strip(),
            'url': self.repo_url.text().strip(),
            'branch': self.branch_combo.currentText().strip(),
            'token': self.token_input.text().strip()
        }
        self.repo_mgr.update(idx, data)
        self._log(f"Profile '{data['name']}' saved", 'success')
        self._show_info("Profile saved")

    # ── Helper Methods ─────────────────────────────────────────────────

    def _log(self, msg, level='info'):
        """Добавить сообщение в лог с иконкой статуса"""
        # Получаем иконку статуса
        status_icon = self.icons.get_status_icon(level) if hasattr(self, 'icons') else None
        
        # Форматируем сообщение с иконкой
        if isinstance(status_icon, str):
            formatted = f"[{status_icon}] {msg}"
        else:
            icon_map = {'success': '', 'warning': '️', 'error': '', 'info': '️'}
            formatted = f"[{icon_map.get(level, '•')}] {msg}"
        
        # Добавляем в QTextEdit
        from datetime import datetime
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_output.append(f"[{timestamp}] {formatted}")
        
        # Авто-прокрутка вниз
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())