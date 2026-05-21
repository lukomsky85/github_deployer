# ui/settings_tab.py
import os
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QComboBox, QPushButton, QGroupBox, QMessageBox, QFileDialog,
    QLabel, QDialog, QDialogButtonBox, QScrollArea, QFrame
)

from utils.crypto import TokenManager
from utils.history import CommitHistoryManager
from utils.lang_manager import lang_mgr
from utils.icon_manager import IconManager


class SettingsTabMixin:

    def _create_settings_tab(self):
        icons = IconManager()
        tab = QWidget()
        root = QVBoxLayout(tab)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        root.addWidget(scroll, 1)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        scroll.setWidget(content)

        # ── Path Settings ─────────────────────────────────────────────
        path_group = QGroupBox(lang_mgr.get_text("settings_tab.path_group"))
        path_lay = QVBoxLayout(path_group)
        path_lay.setSpacing(8)

        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.default_path_input = QLineEdit()
        self.default_path_input.setText(getattr(self, 'default_path', ''))
        form.addRow(lang_mgr.get_text("settings_tab.default_path_label"), self.default_path_input)

        self.default_repo_input = QLineEdit()
        self.default_repo_input.setText(getattr(self, 'default_repo', ''))
        form.addRow(lang_mgr.get_text("settings_tab.default_repo_label"), self.default_repo_input)

        self.default_branch_input = QComboBox()
        self.default_branch_input.addItems(["main", "develop", "master"])
        self.default_branch_input.setCurrentText("main")
        self.default_branch_input.setEditable(True)
        form.addRow(lang_mgr.get_text("settings_tab.default_branch_label"), self.default_branch_input)

        path_lay.addLayout(form)

        browse_path_btn = QPushButton(lang_mgr.get_text("settings_tab.select_button"))
        browse_path_btn.setMinimumWidth(130)
        icons.set_button_icon(browse_path_btn, 'folder', size=QSize(16, 16))
        browse_path_btn.clicked.connect(self._set_default_path)
        path_row = QHBoxLayout()
        path_row.addWidget(browse_path_btn)
        path_row.addStretch()
        path_lay.addLayout(path_row)

        layout.addWidget(path_group)

        # ── Commit History ────────────────────────────────────────────
        history_group = QGroupBox(lang_mgr.get_text("settings_tab.history_group"))
        history_lay = QVBoxLayout(history_group)
        history_lay.setSpacing(8)

        self.history_count_label = QLabel(
            lang_mgr.get_text("settings_tab.total_messages").format(len(self.commit_history))
        )
        self.history_count_label.setStyleSheet("color: #6c6f85; font-size: 9.5pt;")
        history_lay.addWidget(self.history_count_label)

        hist_btns = QHBoxLayout()
        hist_btns.setSpacing(8)

        clear_btn = QPushButton(lang_mgr.get_text("settings_tab.clear_button"))
        clear_btn.setStyleSheet(
            "QPushButton { color:#d20f39; }"
            "QPushButton:hover { border-color:#fca5a5; background:#fff1f2; }"
        )
        icons.set_danger_button_icon(clear_btn, 'clear', size=QSize(16, 16))
        clear_btn.clicked.connect(self._clear_history)
        hist_btns.addWidget(clear_btn)

        export_btn = QPushButton(lang_mgr.get_text("settings_tab.export_button"))
        icons.set_button_icon(export_btn, 'save', size=QSize(16, 16))
        export_btn.clicked.connect(self._export_history)
        hist_btns.addWidget(export_btn)
        hist_btns.addStretch()
        history_lay.addLayout(hist_btns)
        layout.addWidget(history_group)

        # ── Security ──────────────────────────────────────────────────
        security_group = QGroupBox(lang_mgr.get_text("settings_tab.security_group"))
        security_lay = QVBoxLayout(security_group)
        security_lay.setSpacing(10)

        info = TokenManager.storage_info()
        backend_data = {
            'keyring': ('✅', '#40a02b'),
            'fernet':  ('⚠️', '#df8e1d'),
            'none':    ('❌', '#d20f39'),
        }
        icon_text, color = backend_data.get(info['backend'], ('❓', '#8c8fa1'))
        storage_lbl = QLabel(
            f"{icon_text}&nbsp;&nbsp;<b>{lang_mgr.get_text('settings_tab.storage_backend')}:</b>&nbsp;"
            f"<span style='color:{color};'>{info['backend_name']}</span>"
        )
        storage_lbl.setTextFormat(Qt.RichText)
        security_lay.addWidget(storage_lbl)

        if info['has_token']:
            token_lbl = QLabel(
                f"🔑&nbsp;&nbsp;<b>{lang_mgr.get_text('settings_tab.stored_token')}:</b>&nbsp;"
                f"<span style='font-family:Consolas,monospace; color:#89b4fa; font-size:10.5pt;'>"
                f"{info['masked']}</span>"
            )
            token_lbl.setTextFormat(Qt.RichText)
        else:
            token_lbl = QLabel(f"🔑&nbsp;&nbsp;{lang_mgr.get_text('settings_tab.no_stored_token')}")
            token_lbl.setStyleSheet("color: #8c8fa1;")
            token_lbl.setTextFormat(Qt.RichText)
        security_lay.addWidget(token_lbl)

        if info['backend'] == 'fernet':
            hint = QLabel(lang_mgr.get_text("settings_tab.keyring_hint"))
            hint.setWordWrap(True)
            hint.setStyleSheet(
                "background:#fff7ed; border:1px solid #fed7aa; border-radius:6px;"
                " padding:8px; color:#9a3412; font-size:9pt;"
            )
            security_lay.addWidget(hint)

        sec_btns = QHBoxLayout()
        sec_btns.setSpacing(8)

        del_btn = QPushButton(lang_mgr.get_text("settings_tab.delete_token_button"))
        del_btn.setStyleSheet(
            "QPushButton { color:#d20f39; }"
            "QPushButton:hover { border-color:#fca5a5; background:#fff1f2; }"
        )
        icons.set_danger_button_icon(del_btn, 'delete', size=QSize(16, 16))
        del_btn.clicked.connect(self._delete_token)
        sec_btns.addWidget(del_btn)

        check_btn = QPushButton(lang_mgr.get_text("settings_tab.check_token_button"))
        icons.set_button_icon(check_btn, 'token', size=QSize(16, 16))
        check_btn.clicked.connect(self._check_token)
        sec_btns.addWidget(check_btn)
        sec_btns.addStretch()
        security_lay.addLayout(sec_btns)
        layout.addWidget(security_group)
        layout.addStretch()

        # ── Save button — outside scroll, always visible ──────────────
        save_panel = QWidget()
        save_panel.setStyleSheet(
            "QWidget { border-top: 1px solid #dce0e8; background: #f5f7fb; }"
        )
        save_lay = QHBoxLayout(save_panel)
        save_lay.setContentsMargins(12, 10, 12, 10)
        save_lay.addStretch()

        save_btn = QPushButton(lang_mgr.get_text("settings_tab.save_settings_button"))
        save_btn.setMinimumWidth(160)
        save_btn.setMinimumHeight(38)
        save_btn.setStyleSheet(
            "QPushButton { background:#1e66f5; color:#fff; border:none; border-radius:8px;"
            " padding:8px 24px; font-weight:600; font-size:10.5pt; }"
            "QPushButton:hover { background:#1554d4; }"
            "QPushButton:pressed { background:#0e44b4; }"
        )
        icons.set_primary_button_icon(save_btn, 'save', size=QSize(18, 18))
        save_btn.clicked.connect(self._save_settings)
        save_lay.addWidget(save_btn)
        root.addWidget(save_panel)

        return tab

    def _set_default_path(self):
        path = QFileDialog.getExistingDirectory(
            self, lang_mgr.get_text("settings_tab.select_button"),
            self.default_path_input.text()
        )
        if path:
            self.default_path_input.setText(path)

    def _save_settings(self):
        self.default_path = self.default_path_input.text().strip()
        self.default_repo = self.default_repo_input.text().strip()
        if hasattr(self, 'path_input'):
            self.path_input.setText(self.default_path)
        self._save_app_state()
        self._show_info(lang_mgr.get_text("messages.settings_saved"))

    def _manage_token(self):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox
        icons = IconManager()
        dialog = QDialog(self)
        dialog.setWindowTitle(lang_mgr.get_text("dialogs.manage_token.title"))
        dialog.setMinimumWidth(460)
        lay = QVBoxLayout(dialog)
        lay.setSpacing(12)

        info = TokenManager.storage_info()
        backend_data = {'keyring': ('✅','#40a02b'), 'fernet': ('⚠️','#df8e1d'), 'none': ('❌','#d20f39')}
        icon_text, color = backend_data.get(info['backend'], ('❓','#8c8fa1'))

        lbl = QLabel(
            f"{icon_text}&nbsp;&nbsp;<b>{lang_mgr.get_text('settings_tab.storage_backend')}:</b><br>"
            f"<span style='color:{color}; font-size:10pt;'>{info['backend_name']}</span>"
        )
        lbl.setTextFormat(Qt.RichText)
        lay.addWidget(lbl)

        if info['has_token']:
            t = QLabel(
                f"🔑&nbsp;&nbsp;<b>{lang_mgr.get_text('settings_tab.stored_token')}:</b>&nbsp;"
                f"<span style='font-family:Consolas; color:#89b4fa; font-size:11pt;'>{info['masked']}</span>"
            )
            t.setTextFormat(Qt.RichText)
        else:
            t = QLabel(f"🔑&nbsp;&nbsp;{lang_mgr.get_text('settings_tab.no_stored_token')}")
            t.setStyleSheet("color:#8c8fa1;")
        lay.addWidget(t)

        btns = QDialogButtonBox(QDialogButtonBox.Close)
        if info['has_token']:
            del_btn = btns.addButton(lang_mgr.get_text("dialogs.manage_token.delete"),
                                     QDialogButtonBox.DestructiveRole)
            del_btn.setStyleSheet("color:#d20f39;")
            del_btn.clicked.connect(lambda: [self._delete_token(), dialog.accept()])
        btns.rejected.connect(dialog.reject)
        lay.addWidget(btns)
        dialog.exec_()
