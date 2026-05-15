# ui/settings_tab.py
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, 
    QComboBox, QPushButton, QGroupBox, QMessageBox, QFileDialog, 
    QLabel, QDialog, QDialogButtonBox  # <-- Добавлены недостающие импорты
)

from utils.crypto import TokenManager
from utils.history import CommitHistoryManager
from utils.lang_manager import lang_mgr

class SettingsTabMixin:
    """Mixin for Settings tab logic"""
    
    def _create_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        path_group = QGroupBox(lang_mgr.get_text("settings_tab.path_group"))
        path_layout = QFormLayout(path_group)
        
        self.default_path_input = QLineEdit()
        self.default_path_input.setText(self.default_path)
        path_layout.addRow(lang_mgr.get_text("settings_tab.default_path_label"), self.default_path_input)
        
        set_path_btn = QPushButton(lang_mgr.get_text("settings_tab.select_button"))
        set_path_btn.clicked.connect(self._set_default_path)
        path_layout.addRow("", set_path_btn)
        
        self.default_repo_input = QLineEdit()
        self.default_repo_input.setText(self.default_repo)
        path_layout.addRow(lang_mgr.get_text("settings_tab.default_repo_label"), self.default_repo_input)
        
        self.default_branch_input = QComboBox()
        self.default_branch_input.addItems(["main", "develop", "master"])
        self.default_branch_input.setCurrentText("main")
        path_layout.addRow(lang_mgr.get_text("settings_tab.default_branch_label"), self.default_branch_input)
        
        layout.addWidget(path_group)
        
        history_group = QGroupBox(lang_mgr.get_text("settings_tab.history_group"))
        history_layout = QVBoxLayout(history_group)
        
        self.history_count_label = QLabel(lang_mgr.get_text("settings_tab.total_messages").format(len(self.commit_history)))
        history_layout.addWidget(self.history_count_label)
        
        history_buttons = QHBoxLayout()
        clear_history_btn = QPushButton(lang_mgr.get_text("settings_tab.clear_button"))
        clear_history_btn.clicked.connect(self._clear_history)
        history_buttons.addWidget(clear_history_btn)
        
        export_history_btn = QPushButton(lang_mgr.get_text("settings_tab.export_button"))
        export_history_btn.clicked.connect(self._export_history)
        history_buttons.addWidget(export_history_btn)
        history_buttons.addStretch()
        history_layout.addLayout(history_buttons)
        
        layout.addWidget(history_group)
        
        security_group = QGroupBox(lang_mgr.get_text("settings_tab.security_group"))
        security_layout = QVBoxLayout(security_group)
        
        security_buttons = QHBoxLayout()
        delete_token_btn = QPushButton(lang_mgr.get_text("settings_tab.delete_token_button"))
        delete_token_btn.clicked.connect(self._delete_token)
        security_buttons.addWidget(delete_token_btn)
        
        check_token_btn = QPushButton(lang_mgr.get_text("settings_tab.check_token_button"))
        check_token_btn.clicked.connect(self._check_token)
        security_buttons.addWidget(check_token_btn)
        security_buttons.addStretch()
        security_layout.addLayout(security_buttons)
        
        layout.addWidget(security_group)
        
        save_btn = QPushButton(lang_mgr.get_text("settings_tab.save_settings_button"))
        save_btn.clicked.connect(self._save_settings)
        layout.addWidget(save_btn)
        
        layout.addStretch()
        
        return tab
    
    def _set_default_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Default Project Folder", self.default_path_input.text())
        if path:
            self.default_path_input.setText(path)

    def _save_settings(self):
        self.default_path = self.default_path_input.text()
        self.default_repo = self.default_repo_input.text()
        self.path_input.setText(self.default_path)
        self.repo_url.setText(self.default_repo)
        self.branch_combo.setCurrentText(self.default_branch_input.currentText())
        self._log(lang_mgr.get_text("messages.settings_saved"), 'success')

    def _reset_settings(self):
        reply = QMessageBox.question(self, lang_mgr.get_text("buttons.ok"), 
                                    "Reset all settings to defaults?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.default_path = os.getcwd()
            self.default_repo = "https://github.com/username/repository.git"
            self.default_path_input.setText(self.default_path)
            self.default_repo_input.setText(self.default_repo)
            self.path_input.setText(self.default_path)
            self.repo_url.setText(self.default_repo)
            self._log("🔄 Settings reset to defaults", 'warning')

    def _clear_history(self):
        reply = QMessageBox.question(self, lang_mgr.get_text("buttons.ok"), 
                                    lang_mgr.get_text("dialogs.delete_branch.confirm").format("history"),
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if os.path.exists(CommitHistoryManager.HISTORY_FILE):
                os.remove(CommitHistoryManager.HISTORY_FILE)
            self.commit_history = []
            self.commit_combo.clear()
            self.history_count_label.setText(lang_mgr.get_text("settings_tab.total_messages").format(0))
            self._log(lang_mgr.get_text("messages.history_cleared"), 'warning')

    def _export_history(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export History", "", "Text Files (*.txt);;JSON Files (*.json)"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("GitHub Deploy Helper - Commit History\n")
                    f.write("=" * 40 + "\n\n")
                    for i, msg in enumerate(self.commit_history, 1):
                        f.write(f"{i}. {msg}\n")
                self._log(lang_mgr.get_text("messages.history_exported").format(file_path), 'success')
            except Exception as e:
                self._log(lang_mgr.get_text("messages.export_failed").format(e), 'error')

    def _delete_token(self):
        reply = QMessageBox.question(self, lang_mgr.get_text("buttons.ok"), 
                                    lang_mgr.get_text("dialogs.delete_branch.confirm").format("token"),
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            TokenManager.delete_token()
            self.token_input.clear()
            self._log(lang_mgr.get_text("messages.token_deleted"), 'warning')
            self._update_token_status()
            QMessageBox.information(self, lang_mgr.get_text("buttons.ok"), lang_mgr.get_text("messages.token_deleted_done"))

    def _check_token(self):
        token = self.token_input.text().strip()
        if not token:
            QMessageBox.warning(self, lang_mgr.get_text("buttons.ok"), lang_mgr.get_text("errors.no_token"))
            return
        
        valid_prefixes = ['ghp_', 'gho_', 'ghu_', 'ghs_', 'ghr_', 'github_pat_']
        if any(token.startswith(p) for p in valid_prefixes):
            QMessageBox.information(self, lang_mgr.get_text("buttons.ok"), lang_mgr.get_text("messages.token_check_correct"))
        else:
            QMessageBox.warning(self, lang_mgr.get_text("buttons.ok"), lang_mgr.get_text("messages.token_check_unusual"))

    def _manage_token(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(lang_mgr.get_text("dialogs.manage_token.title"))
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout(dialog)
        
        current_token = TokenManager.load_token()
        status = lang_mgr.get_text("dialogs.manage_token.status_saved") if current_token else lang_mgr.get_text("dialogs.manage_token.status_not_saved")
        layout.addWidget(QLabel(f"Status: {status}"))
        
        if current_token:
            masked = f"{current_token[:8]}...{current_token[-4:]}"
            layout.addWidget(QLabel(lang_mgr.get_text("dialogs.manage_token.token_masked").format(masked)))
        
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        if current_token:
            delete_btn = buttons.addButton(lang_mgr.get_text("dialogs.manage_token.delete"), QDialogButtonBox.DestructiveRole)
            delete_btn.clicked.connect(lambda: [self._delete_token(), dialog.accept()])
        
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.exec_()