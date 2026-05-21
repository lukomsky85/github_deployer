# ui/gitignore_tab.py
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTextEdit, QGroupBox, QMessageBox, QLabel, QFrame, QScrollArea
)
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QFont

from utils.lang_manager import lang_mgr
from utils.icon_manager import IconManager
from config import DEFAULT_GITIGNORE


class GitignoreTabMixin:

    def _create_gitignore_tab(self):
        icons = IconManager()
        tab = QWidget()
        root = QVBoxLayout(tab)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        root.addWidget(scroll)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        scroll.setWidget(content)

        # ── Project path ──────────────────────────────────────────────
        project_group = QGroupBox(lang_mgr.get_text("gitignore_tab.project_group"))
        pg_lay = QHBoxLayout(project_group)
        pg_lay.setSpacing(6)

        self.gitignore_path = QLineEdit()
        self.gitignore_path.setPlaceholderText(lang_mgr.get_text("gitignore_tab.path_placeholder"))
        if hasattr(self, 'default_path'):
            self.gitignore_path.setText(self.default_path)
        pg_lay.addWidget(self.gitignore_path)

        browse_btn = QPushButton()
        browse_btn.setFixedSize(36, 36)
        browse_btn.setToolTip(lang_mgr.get_text("gitignore_tab.browse_tooltip"))
        browse_btn.setStyleSheet("QPushButton { padding: 4px; }")
        icons.set_button_icon(browse_btn, 'folder', size=QSize(20, 20))
        browse_btn.clicked.connect(lambda: self._browse_folder(self.gitignore_path))
        pg_lay.addWidget(browse_btn)

        load_btn = QPushButton(lang_mgr.get_text("gitignore_tab.load_button"))
        load_btn.setMinimumWidth(150)
        load_btn.setStyleSheet(
            "QPushButton { background:#e8f0fe; color:#1e66f5; border:1px solid #b8d0fb; }"
            "QPushButton:hover { background:#d0e4fd; }"
        )
        icons.set_button_icon(load_btn, 'fetch', color='#1e66f5', size=QSize(16, 16))
        load_btn.clicked.connect(self._load_gitignore)
        pg_lay.addWidget(load_btn)

        sync_btn = QPushButton(lang_mgr.get_text("gitignore_tab.sync_button"))
        sync_btn.setMinimumWidth(160)
        sync_btn.setStyleSheet(
            "QPushButton { background:#e8f0fe; color:#1e66f5; border:1px solid #b8d0fb; }"
            "QPushButton:hover { background:#d0e4fd; }"
        )
        icons.set_button_icon(sync_btn, 'refresh', color='#1e66f5', size=QSize(16, 16))
        sync_btn.clicked.connect(self._sync_gitignore_path)
        pg_lay.addWidget(sync_btn)

        layout.addWidget(project_group)

        # ── Editor ────────────────────────────────────────────────────
        editor_group = QGroupBox(lang_mgr.get_text("gitignore_tab.editor_group"))
        eg_lay = QVBoxLayout(editor_group)
        eg_lay.setSpacing(6)

        self.gitignore_editor = QTextEdit()
        self.gitignore_editor.setFont(QFont("Consolas", 10))
        self.gitignore_editor.setPlaceholderText(lang_mgr.get_text("gitignore_tab.editor_placeholder"))
        self.gitignore_editor.setMinimumHeight(260)
        self.gitignore_editor.setStyleSheet(
            "QTextEdit { background:#f8f9fc; border:1px solid #dce0e8;"
            " border-radius:7px; padding:8px; font-family:Consolas,monospace; }"
            "QTextEdit:focus { border-color:#1e66f5; }"
        )
        eg_lay.addWidget(self.gitignore_editor)

        hint = QLabel(lang_mgr.get_text("gitignore_tab.editor_hint"))
        hint.setStyleSheet("color:#df8e1d; font-size:8.5pt;")
        eg_lay.addWidget(hint)

        layout.addWidget(editor_group, 1)

        # ── Actions ───────────────────────────────────────────────────
        actions_group = QGroupBox(lang_mgr.get_text("gitignore_tab.actions_group"))
        al = QHBoxLayout(actions_group)
        al.setSpacing(8)

        reset_btn = QPushButton(lang_mgr.get_text("gitignore_tab.reset_button"))
        icons.set_button_icon(reset_btn, 'refresh', size=QSize(16, 16))
        reset_btn.clicked.connect(self._reset_gitignore)
        al.addWidget(reset_btn)

        save_btn = QPushButton(lang_mgr.get_text("gitignore_tab.save_button"))
        save_btn.setStyleSheet(
            "QPushButton { background:#1e66f5; color:#fff; border:none; border-radius:7px;"
            " padding:7px 18px; font-weight:600; }"
            "QPushButton:hover { background:#1554d4; }"
            "QPushButton:disabled { background:#9bb8f5; }"
        )
        icons.set_primary_button_icon(save_btn, 'save', size=QSize(16, 16))
        save_btn.clicked.connect(self._save_gitignore)
        al.addWidget(save_btn)

        al.addStretch()
        layout.addWidget(actions_group)

        return tab

    def _sync_gitignore_path(self):
        if hasattr(self, 'path_input'):
            self.gitignore_path.setText(self.path_input.text())

    def _load_gitignore(self):
        path = self.gitignore_path.text().strip()
        if not path or not os.path.isdir(path):
            self._show_error(lang_mgr.get_text("errors.folder_not_found"),
                             lang_mgr.get_text("messages.folder_not_found").format(path))
            return
        gi = os.path.join(path, '.gitignore')
        if os.path.exists(gi):
            self.gitignore_editor.setPlainText(open(gi, encoding='utf-8', errors='replace').read())
            self._log(lang_mgr.get_text("messages.gitignore_loaded"), 'success')
        else:
            self.gitignore_editor.setPlainText(DEFAULT_GITIGNORE)
            self._log(lang_mgr.get_text("messages.gitignore_not_found"), 'warning')

    def _reset_gitignore(self):
        self.gitignore_editor.setPlainText(DEFAULT_GITIGNORE)

    def _save_gitignore(self):
        path = self.gitignore_path.text().strip()
        if not path or not os.path.isdir(path):
            self._show_error(lang_mgr.get_text("errors.folder_not_found"),
                             lang_mgr.get_text("messages.folder_not_found").format(path))
            return
        gi = os.path.join(path, '.gitignore')
        try:
            with open(gi, 'w', encoding='utf-8') as f:
                f.write(self.gitignore_editor.toPlainText())
            self._log(lang_mgr.get_text("messages.gitignore_saved").format(gi), 'success')
            self._show_info(lang_mgr.get_text("messages.gitignore_saved").format(gi))
        except Exception as e:
            self._show_error(lang_mgr.get_text("errors.save_failed"), str(e))

    def _preview_gitignore(self):
        """Показывает текущий .gitignore в диалоге (вызывается из Deploy tab)."""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox
        from PyQt5.QtGui import QFont

        path = self.path_input.text().strip() if hasattr(self, 'path_input') else ''
        gi_path = os.path.join(path, '.gitignore') if path else ''

        dlg = QDialog(self)
        dlg.setWindowTitle('.gitignore')
        dlg.setMinimumSize(500, 400)
        lay = QVBoxLayout(dlg)

        editor = QTextEdit()
        editor.setFont(QFont('Consolas', 10))
        editor.setReadOnly(True)
        editor.setStyleSheet(
            "QTextEdit { background:#f8f9fc; border:1px solid #dce0e8;"
            " border-radius:7px; padding:8px; }"
        )

        if gi_path and os.path.exists(gi_path):
            editor.setPlainText(open(gi_path, encoding='utf-8', errors='replace').read())
        else:
            editor.setPlainText(
                f"# {lang_mgr.get_text('messages.gitignore_not_found')}\n\n"
                + __import__('config').DEFAULT_GITIGNORE
            )

        lay.addWidget(editor)
        btns = QDialogButtonBox(QDialogButtonBox.Close)
        btns.rejected.connect(dlg.reject)
        lay.addWidget(btns)
        dlg.exec_()
