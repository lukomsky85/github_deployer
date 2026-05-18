# ui/gitignore_tab.py
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTextEdit, QGroupBox, QMessageBox, QDialog, QFormLayout, QLabel
)
from PyQt5.QtGui import QFont  # <-- Перенесено сюда из QtWidgets

from utils.gitignore import GitignoreManager
from config import DEFAULT_GITIGNORE
from utils.lang_manager import lang_mgr

class GitignoreTabMixin:
    """Mixin for .gitignore tab logic"""
    
    def _create_gitignore_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        project_group = QGroupBox("Select Project")
        project_layout = QHBoxLayout(project_group)
        
        self.gitignore_path = QLineEdit()
        self.gitignore_path.setText(self.default_path)
        project_layout.addWidget(self.gitignore_path)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(lambda: self._browse_folder(self.gitignore_path))
        project_layout.addWidget(browse_btn)
        
        load_btn = QPushButton(" Load .gitignore")
        load_btn.clicked.connect(self._load_gitignore_content)
        project_layout.addWidget(load_btn)
        
        layout.addWidget(project_group)
        
        editor_group = QGroupBox(".gitignore Editor")
        editor_layout = QVBoxLayout(editor_group)
        
        self.gitignore_editor = QTextEdit()
        self.gitignore_editor.setFont(QFont("Consolas", 10))
        self.gitignore_editor.setPlaceholderText("Select a project and click 'Load .gitignore' to start editing...")
        editor_layout.addWidget(self.gitignore_editor)
        
        layout.addWidget(editor_group)
        
        buttons_group = QGroupBox("Actions")
        buttons_layout = QHBoxLayout(buttons_group)
        
        reset_btn = QPushButton(" Reset to Default")
        reset_btn.clicked.connect(self._reset_gitignore_to_default)
        buttons_layout.addWidget(reset_btn)
        
        buttons_layout.addStretch()
        
        save_btn = QPushButton(" Save .gitignore")
        save_btn.clicked.connect(self._save_gitignore_content)
        save_btn.setStyleSheet("background-color: #1e66f5; color: white;")
        buttons_layout.addWidget(save_btn)
        
        layout.addWidget(buttons_group)
        
        info_label = QLabel(" Tip: .gitignore tells Git which files to ignore. Edit carefully!")
        info_label.setStyleSheet("color: #df8e1d; font-size: 8pt; padding: 5px;")
        layout.addWidget(info_label)
        
        return tab
    
    def _load_gitignore_content(self):
        path = self.gitignore_path.text().strip()
        if not os.path.isdir(path):
            QMessageBox.warning(self, lang_mgr.get_text("errors.folder_not_found"), "Project folder not found")
            return
        
        content = GitignoreManager.load(path)
        self.gitignore_editor.setPlainText(content)
        
        gitignore_path = os.path.join(path, '.gitignore')
        if os.path.exists(gitignore_path):
            self._log(f" Loaded .gitignore from {path}", 'success')
        else:
            self._log(f" Created new .gitignore template for {path}", 'info')

    def _save_gitignore_content(self):
        path = self.gitignore_path.text().strip()
        if not os.path.isdir(path):
            QMessageBox.warning(self, lang_mgr.get_text("errors.folder_not_found"), "Project folder not found")
            return
        
        content = self.gitignore_editor.toPlainText()
        success, message = GitignoreManager.save(path, content)
        
        if success:
            self._log(message, 'success')
            QMessageBox.information(self, lang_mgr.get_text("buttons.ok"), message)
        else:
            self._log(message, 'error')
            QMessageBox.critical(self, lang_mgr.get_text("errors.deploy_failed"), message)

    def _reset_gitignore_to_default(self):
        reply = QMessageBox.question(self, lang_mgr.get_text("buttons.ok"), 
                                    "Reset .gitignore to default template?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.gitignore_editor.setPlainText(DEFAULT_GITIGNORE)
            self._log(" .gitignore reset to default template", 'info')

    def _preview_gitignore(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(lang_mgr.get_text("dialogs.preview_gitignore.title"))
        dialog.setMinimumSize(700, 600)
        
        layout = QVBoxLayout(dialog)
        
        info_label = QLabel(f"Editing .gitignore for: {self.path_input.text()}")
        info_label.setStyleSheet("font-weight: bold; color: #1e66f5;")
        layout.addWidget(info_label)
        
        editor = QTextEdit()
        editor.setFont(QFont("Consolas", 10))
        editor.setPlainText(GitignoreManager.load(self.path_input.text()))
        layout.addWidget(editor)
        
        button_layout = QHBoxLayout()
        
        reset_btn = QPushButton(" Reset to Default")
        reset_btn.clicked.connect(lambda: editor.setPlainText(DEFAULT_GITIGNORE))
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        save_btn = QPushButton(" Save")
        save_btn.clicked.connect(lambda: self._save_gitignore_content_from_dialog(editor, self.path_input.text()))
        save_btn.setStyleSheet("background-color: #1e66f5; color: white;")
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton(" Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        dialog.exec_()

    def _save_gitignore_content_from_dialog(self, editor, path):
        content = editor.toPlainText()
        success, message = GitignoreManager.save(path, content)
        if success:
            QMessageBox.information(self, lang_mgr.get_text("buttons.ok"), message)
        else:
            QMessageBox.critical(self, lang_mgr.get_text("errors.deploy_failed"), message)