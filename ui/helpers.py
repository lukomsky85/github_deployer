# ui/helpers.py
import os
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QLabel, QLineEdit, QDialog, QDialogButtonBox, QVBoxLayout, QApplication
from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import QTimer
from datetime import datetime

from utils.git_helper import GitHelper
from utils.lang_manager import lang_mgr

class HelpersMixin:
    """Mixin для вспомогательных методов"""
    
    def _sync_paths(self):
        p = self.path_input.text()
        self.branch_path.setText(p)
        self.gitignore_path.setText(p)

    def _browse_folder(self, line_edit):
        path = QFileDialog.getExistingDirectory(self, lang_mgr.get_text("menu.select_project"), line_edit.text())
        if path:
            line_edit.setText(path)
            if line_edit == self.path_input:
                self._refresh_branches()

    def _refresh_branches(self):
        path = self.path_input.text().strip()
        if not os.path.isdir(path):
            self._log(lang_mgr.get_text("messages.folder_not_found").format(path), 'error')
            return
        
        if not GitHelper.is_git_repo(path):
            self._log(lang_mgr.get_text("messages.not_git_repo"), 'warning')
            return
        
        branches = GitHelper.get_branches(path)
        self.branch_combo.clear()
        self.branch_combo.addItems(branches)
        
        current = GitHelper.get_current_branch(path)
        self.branch_combo.setCurrentText(current)
        
        self._log(lang_mgr.get_text("messages.branches_loaded").format(', '.join(branches)), 'success')

    def _paste_token(self):
        clipboard = QApplication.clipboard()
        token = clipboard.text().strip()
        
        if not token:
            QMessageBox.warning(self, lang_mgr.get_text("buttons.ok"), lang_mgr.get_text("messages.clipboard_empty"))
            return
        
        valid_prefixes = ['ghp_', 'gho_', 'ghu_', 'ghs_', 'ghr_', 'github_pat_']
        if not any(token.startswith(p) for p in valid_prefixes):
            reply = QMessageBox.question(self, lang_mgr.get_text("buttons.ok"), 
                                        lang_mgr.get_text("messages.token_format_warning"),
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
        
        self.token_input.setText(token)
        self._log(lang_mgr.get_text("messages.token_pasted"), 'success')
        
        self.token_input.setEchoMode(QLineEdit.Normal)
        QTimer.singleShot(3000, lambda: self.token_input.setEchoMode(QLineEdit.Password))
        
        self._update_token_status()

    def _load_saved_token(self):
        from utils.crypto import TokenManager
        token = TokenManager.load_token()
        if token:
            self.token_input.setText(token)
            self._log(lang_mgr.get_text("messages.token_loaded"), 'success')
            self._update_token_status()

    def _log(self, message, level='info'):
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        colors = {
            'info': '#4c4f69',
            'success': '#40a02b',
            'warning': '#df8e1d',
            'error': '#d20f39'
        }
        
        prefixes = {
            'info': '',
            'success': '✅ ',
            'warning': '⚠️ ',
            'error': '❌ '
        }
        
        color = colors.get(level, '#4c4f69')
        prefix = prefixes.get(level, '')
        
        formatted_msg = f'<span style="color: {color};">[{timestamp}] {prefix}{message}</span>'
        
        self.log_output.moveCursor(QTextCursor.End)
        self.log_output.insertHtml(formatted_msg + '<br>')
        self.log_output.moveCursor(QTextCursor.End)
        
        print(f"[{timestamp}] [{level.upper()}] {message}")

    def _clear_log(self):
        self.log_output.clear()
        self._log(lang_mgr.get_text("messages.log_cleared"), 'info')

    def _save_log(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Log", "", "Log Files (*.log);;Text Files (*.txt);;All Files (*.*)"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_output.toPlainText())
                self._log(lang_mgr.get_text("messages.log_saved").format(file_path), 'success')
            except Exception as e:
                self._log(lang_mgr.get_text("messages.log_save_failed").format(e), 'error')

    def _add_custom_commit(self):
        from utils.history import CommitHistoryManager
        
        dialog = QDialog(self)
        dialog.setWindowTitle(lang_mgr.get_text("dialogs.add_commit.title"))
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(lang_mgr.get_text("dialogs.add_commit.label")))
        
        input_field = QLineEdit()
        layout.addWidget(input_field)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText(lang_mgr.get_text("buttons.ok"))
        buttons.button(QDialogButtonBox.Cancel).setText(lang_mgr.get_text("buttons.cancel"))
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            msg = input_field.text().strip()
            if msg:
                CommitHistoryManager.save_message(msg)
                self.commit_history = CommitHistoryManager.load_history()
                self.commit_combo.clear()
                self.commit_combo.addItems(self.commit_history)
                self.commit_combo.setCurrentText(msg)
                self.history_count_label.setText(lang_mgr.get_text("settings_tab.total_messages").format(len(self.commit_history)))
                self._log(lang_mgr.get_text("dialogs.add_commit.success").format(msg), 'success')

    def _confirm(self, message):
        return QMessageBox.question(self, lang_mgr.get_text("buttons.ok"), message,
                                   QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes

    def _show_info(self, message):
        QMessageBox.information(self, lang_mgr.get_text("buttons.ok"), message)

    def _show_warning(self, title, message):
        QMessageBox.warning(self, title, message)

    def _show_error(self, title, message):
        QMessageBox.critical(self, title, message)