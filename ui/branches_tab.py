# ui/branches_tab.py
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QGroupBox, QTreeWidget, QTreeWidgetItem, QMessageBox,
    QDialog, QFormLayout, QComboBox, QDialogButtonBox, QLabel,
    QFrame, QSizePolicy, QScrollArea
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, QSize

from utils.git_helper import GitHelper
from utils.lang_manager import lang_mgr
from ui.dialogs import BranchDialog
from utils.icon_manager import IconManager


class BranchesTabMixin:

    def _create_branches_tab(self):
        icons = IconManager()
        tab = QWidget()
        tab.setStyleSheet("QWidget#branches_root { background: #eff1f5; }")

        root = QVBoxLayout(tab)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # ── Select Project ────────────────────────────────────────────
        project_group = QGroupBox(lang_mgr.get_text("branches_tab.project_group"))
        pg = QHBoxLayout(project_group)
        pg.setContentsMargins(12, 8, 12, 8)
        pg.setSpacing(8)

        self.branch_path = QLineEdit()
        self.branch_path.setText(getattr(self, 'default_path', ''))
        self.branch_path.setPlaceholderText(lang_mgr.get_text("branches_tab.path_placeholder"))
        pg.addWidget(self.branch_path)

        browse_btn = QPushButton()
        browse_btn.setFixedSize(36, 36)
        browse_btn.setToolTip(lang_mgr.get_text("branches_tab.browse_button"))
        browse_btn.setStyleSheet("QPushButton { padding: 4px; }")
        icons.set_button_icon(browse_btn, 'folder', size=QSize(20, 20))
        browse_btn.clicked.connect(lambda: self._browse_folder(self.branch_path))
        pg.addWidget(browse_btn)

        sync_btn = QPushButton(lang_mgr.get_text("branches_tab.sync_button"))
        sync_btn.setMinimumWidth(130)
        sync_btn.setStyleSheet(
            "QPushButton { background:#f0f4ff; color:#1e66f5;"
            " border:1px solid #b8d0fb; border-radius:7px; padding:6px 14px; }"
            "QPushButton:hover { background:#e8f0fe; }"
        )
        icons.set_button_icon(sync_btn, 'refresh', color='#1e66f5', size=QSize(14, 14))
        sync_btn.clicked.connect(lambda: self.branch_path.setText(
            self.path_input.text() if hasattr(self, 'path_input') else ''
        ))
        pg.addWidget(sync_btn)

        load_btn = QPushButton(lang_mgr.get_text("branches_tab.load_button"))
        load_btn.setMinimumWidth(150)
        load_btn.setStyleSheet(
            "QPushButton { background:#1e66f5; color:#fff; border:none;"
            " border-radius:7px; padding:7px 16px; font-weight:600; }"
            "QPushButton:hover { background:#1554d4; }"
        )
        icons.set_primary_button_icon(load_btn, 'refresh', size=QSize(16, 16))
        load_btn.clicked.connect(self._load_branches_info)
        pg.addWidget(load_btn)

        root.addWidget(project_group)

        # ── Current Branch ────────────────────────────────────────────
        current_group = QGroupBox(lang_mgr.get_text("branches_tab.current_group"))
        cl = QHBoxLayout(current_group)
        cl.setContentsMargins(12, 8, 12, 8)

        branch_icon_lbl = QLabel()
        _ic = icons.get('branch', color='#1e66f5', size=QSize(18, 18))
        if _ic:
            branch_icon_lbl.setPixmap(_ic.pixmap(QSize(18, 18)))
        cl.addWidget(branch_icon_lbl)

        self.current_branch_label = QLabel(lang_mgr.get_text("branches_tab.not_loaded"))
        self.current_branch_label.setStyleSheet(
            "font-weight:600; color:#1e66f5; font-size:11pt; padding-left:4px;"
        )
        cl.addWidget(self.current_branch_label)
        cl.addStretch()
        root.addWidget(current_group)

        # ── Branches list ─────────────────────────────────────────────
        branches_group = QGroupBox(lang_mgr.get_text("branches_tab.branches_group"))
        bl = QVBoxLayout(branches_group)
        bl.setContentsMargins(12, 8, 12, 8)

        self.branches_tree = QTreeWidget()
        self.branches_tree.setHeaderLabels([
            lang_mgr.get_text("branches_tab.branch_header"),
            lang_mgr.get_text("branches_tab.commit_header"),
        ])
        self.branches_tree.setColumnWidth(0, 220)
        self.branches_tree.setAlternatingRowColors(True)
        self.branches_tree.setSortingEnabled(True)
        self.branches_tree.setRootIsDecorated(False)
        self.branches_tree.setFrameShape(QFrame.NoFrame)
        bl.addWidget(self.branches_tree)
        root.addWidget(branches_group, 1)

        # ── Actions ───────────────────────────────────────────────────
        actions_group = QGroupBox(lang_mgr.get_text("branches_tab.actions_group"))
        al = QHBoxLayout(actions_group)
        al.setContentsMargins(12, 8, 12, 8)
        al.setSpacing(8)

        for label_key, icon_name, slot in [
            ("branches_tab.create_button", "add",     lambda: self._handle_branch_action('create')),
            ("branches_tab.switch_button", "refresh", self._switch_to_selected_branch),
            ("branches_tab.merge_button",  "branch",  lambda: self._handle_branch_action('merge')),
        ]:
            btn = QPushButton(lang_mgr.get_text(label_key))
            icons.set_button_icon(btn, icon_name, size=QSize(16, 16))
            btn.clicked.connect(slot)
            al.addWidget(btn)

        del_btn = QPushButton(lang_mgr.get_text("branches_tab.delete_button"))
        del_btn.setStyleSheet(
            "QPushButton { color:#d20f39; }"
            "QPushButton:hover { border-color:#fca5a5; background:#fff1f2; }"
        )
        icons.set_danger_button_icon(del_btn, 'delete', size=QSize(16, 16))
        del_btn.clicked.connect(self._delete_selected_branch)
        al.addWidget(del_btn)
        al.addStretch()

        root.addWidget(actions_group)
        return tab

    # ── Logic ─────────────────────────────────────────────────────────

    def _load_branches_info(self):
        path = self.branch_path.text().strip()
        if not os.path.isdir(path):
            self._show_error(lang_mgr.get_text("errors.folder_not_found"),
                             lang_mgr.get_text("messages.folder_not_found").format(path))
            return
        if not GitHelper.is_git_repo(path):
            self._show_warning(lang_mgr.get_text("errors.not_git_repo"),
                               lang_mgr.get_text("errors.not_git_repo"))
            return
        self.branches_tree.clear()
        current = GitHelper.get_current_branch(path)
        self.current_branch_label.setText(f"  {current}")
        for branch in GitHelper.get_branches(path):
            last = GitHelper.get_last_commit(path, branch)
            item = QTreeWidgetItem([branch, last])
            if branch == current:
                item.setBackground(0, QColor('#dbeafe'))
                item.setBackground(1, QColor('#dbeafe'))
                item.setForeground(0, QColor('#1e66f5'))
            self.branches_tree.addTopLevelItem(item)
        self._log(lang_mgr.get_text("messages.branches_info_loaded").format(
            len(GitHelper.get_branches(path))), 'success')

    def _handle_branch_action(self, action):
        path = self.branch_path.text().strip()
        if not os.path.isdir(path) or not GitHelper.is_git_repo(path):
            self._show_warning(lang_mgr.get_text("errors.not_git_repo"),
                               lang_mgr.get_text("errors.not_git_repo"))
            return
        if action == 'create':
            dlg = BranchDialog(self, path, 'create')
            if dlg.exec_() == QDialog.Accepted:
                name = dlg.get_data()
                if name:
                    ok, err = GitHelper.run_cmd(['checkout', '-b', name], path, self._log)
                    level = 'success' if ok else 'error'
                    key = "dialogs.create_branch.success" if ok else "dialogs.create_branch.error"
                    self._log(lang_mgr.get_text(key).format(name if ok else err), level)
                    if ok:
                        self._refresh_branches()
                        self._load_branches_info()
        elif action == 'merge':
            branches = GitHelper.get_branches(path)
            dlg = QDialog(self)
            dlg.setWindowTitle(lang_mgr.get_text("dialogs.merge_branches.title"))
            dlg.setMinimumWidth(360)
            lay = QFormLayout(dlg)
            lay.setSpacing(10)
            src = QComboBox(); src.addItems(branches)
            tgt = QComboBox(); tgt.addItems(branches)
            lay.addRow(lang_mgr.get_text("dialogs.merge_branches.source_label"), src)
            lay.addRow(lang_mgr.get_text("dialogs.merge_branches.target_label"), tgt)
            btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            btns.accepted.connect(dlg.accept)
            btns.rejected.connect(dlg.reject)
            lay.addRow(btns)
            if dlg.exec_() == QDialog.Accepted and src.currentText() != tgt.currentText():
                ok, err = GitHelper.merge_branch(path, src.currentText(), tgt.currentText(), self._log)
                if ok:
                    self._log(lang_mgr.get_text("dialogs.merge_branches.success").format(
                        src.currentText(), tgt.currentText()), 'success')
                    self._refresh_branches()
                else:
                    self._log(lang_mgr.get_text("dialogs.merge_branches.error").format(err), 'error')

    def _switch_to_selected_branch(self):
        sel = self.branches_tree.selectedItems()
        if not sel:
            self._show_warning(lang_mgr.get_text("buttons.ok"),
                               lang_mgr.get_text("messages.select_branch_warning"))
            return
        branch = sel[0].text(0)
        path = self.branch_path.text().strip()
        ok, err = GitHelper.run_cmd(['checkout', branch], path, self._log)
        if ok:
            self.current_branch_label.setText(f"  {branch}")
            self._load_branches_info()
            self._refresh_branches()
        else:
            self._log(lang_mgr.get_text("dialogs.switch_branch.error").format(err), 'error')

    def _delete_selected_branch(self):
        sel = self.branches_tree.selectedItems()
        if not sel:
            self._show_warning(lang_mgr.get_text("buttons.ok"),
                               lang_mgr.get_text("messages.select_branch_warning"))
            return
        branch = sel[0].text(0)
        path = self.branch_path.text().strip()
        if branch == GitHelper.get_current_branch(path):
            self._show_warning(lang_mgr.get_text("buttons.ok"),
                               lang_mgr.get_text("dialogs.delete_branch.cannot_delete_current"))
            return
        reply = QMessageBox.question(
            self, lang_mgr.get_text("buttons.ok"),
            lang_mgr.get_text("dialogs.delete_branch.confirm").format(branch),
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            ok, err = GitHelper.run_cmd(['branch', '-d', branch], path, self._log)
            if ok:
                self._log(lang_mgr.get_text("dialogs.delete_branch.success").format(branch), 'success')
                self._load_branches_info()
                self._refresh_branches()
            else:
                self._log(lang_mgr.get_text("dialogs.delete_branch.error").format(err), 'error')
