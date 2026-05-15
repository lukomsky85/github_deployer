# ui/branches_tab.py
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QGroupBox, QTreeWidget, QTreeWidgetItem, QMessageBox,
    QDialog, QFormLayout, QComboBox, QDialogButtonBox, QLabel,
    QSizePolicy
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt

from utils.git_helper import GitHelper
from utils.lang_manager import lang_mgr
from ui.dialogs import BranchDialog


class BranchesTabMixin:
    """Mixin for Branches tab"""

    def _create_branches_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Project path row
        project_group = QGroupBox(lang_mgr.get_text("branches_tab.project_group"))
        project_layout = QHBoxLayout(project_group)
        project_layout.setSpacing(6)

        self.branch_path = QLineEdit()
        self.branch_path.setText(self.default_path)
        project_layout.addWidget(self.branch_path)

        browse_btn = QPushButton(lang_mgr.get_text("branches_tab.browse_button"))
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(lambda: self._browse_folder(self.branch_path))
        project_layout.addWidget(browse_btn)

        load_btn = QPushButton(lang_mgr.get_text("branches_tab.load_button"))
        load_btn.setFixedWidth(110)
        load_btn.setStyleSheet(
            "QPushButton { background-color: #e8f0fe; color: #1e66f5; border-color: #b8d0fb; }"
            "QPushButton:hover { background-color: #d0e4fd; }"
        )
        load_btn.clicked.connect(self._load_branches_info)
        project_layout.addWidget(load_btn)

        layout.addWidget(project_group)

        # Current branch badge
        current_group = QGroupBox(lang_mgr.get_text("branches_tab.current_group"))
        current_layout = QHBoxLayout(current_group)
        self.current_branch_label = QLabel(lang_mgr.get_text("branches_tab.not_loaded"))
        self.current_branch_label.setStyleSheet(
            "font-weight: 600; color: #1e66f5; font-size: 11pt; padding: 2px 0;"
        )
        current_layout.addWidget(self.current_branch_label)
        current_layout.addStretch()
        layout.addWidget(current_group)

        # Branches tree
        branches_group = QGroupBox(lang_mgr.get_text("branches_tab.branches_group"))
        branches_layout = QVBoxLayout(branches_group)

        self.branches_tree = QTreeWidget()
        self.branches_tree.setHeaderLabels([
            lang_mgr.get_text("branches_tab.branch_header"),
            lang_mgr.get_text("branches_tab.commit_header")
        ])
        self.branches_tree.setColumnWidth(0, 220)
        self.branches_tree.setAlternatingRowColors(True)
        self.branches_tree.setSortingEnabled(True)
        self.branches_tree.setRootIsDecorated(False)
        branches_layout.addWidget(self.branches_tree)
        layout.addWidget(branches_group, 1)

        # Actions
        actions_group = QGroupBox(lang_mgr.get_text("branches_tab.actions_group"))
        actions_layout = QHBoxLayout(actions_group)
        actions_layout.setSpacing(8)

        for label, action in [
            (lang_mgr.get_text("branches_tab.create_button"), lambda: self._handle_branch_action('create')),
            (lang_mgr.get_text("branches_tab.switch_button"), self._switch_to_selected_branch),
            (lang_mgr.get_text("branches_tab.merge_button"),  lambda: self._handle_branch_action('merge')),
        ]:
            btn = QPushButton(label)
            btn.clicked.connect(action)
            actions_layout.addWidget(btn)

        delete_btn = QPushButton(lang_mgr.get_text("branches_tab.delete_button"))
        delete_btn.setStyleSheet(
            "QPushButton { color: #d20f39; } QPushButton:hover { border-color: #d20f39; color: #d20f39; }"
        )
        delete_btn.clicked.connect(self._delete_selected_branch)
        actions_layout.addWidget(delete_btn)
        actions_layout.addStretch()

        layout.addWidget(actions_group)
        return tab

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
        current_branch = GitHelper.get_current_branch(path)
        self.current_branch_label.setText(f"  {current_branch}")

        branches = GitHelper.get_branches(path)
        for branch in branches:
            last_commit = GitHelper.get_last_commit(path, branch)
            item = QTreeWidgetItem([branch, last_commit])
            if branch == current_branch:
                item.setBackground(0, QColor('#dbeafe'))
                item.setBackground(1, QColor('#dbeafe'))
                item.setForeground(0, QColor('#1e66f5'))
                item.setToolTip(0, "Current branch")
            self.branches_tree.addTopLevelItem(item)

        self._log(lang_mgr.get_text("messages.branches_info_loaded").format(len(branches)), 'success')

    def _handle_branch_action(self, action):
        path = self.path_input.text().strip()
        if not os.path.isdir(path):
            self._show_error(lang_mgr.get_text("errors.folder_not_found"),
                             lang_mgr.get_text("messages.folder_not_found").format(path))
            return
        if not GitHelper.is_git_repo(path):
            self._show_warning(lang_mgr.get_text("errors.not_git_repo"),
                               lang_mgr.get_text("errors.not_git_repo"))
            return

        if action == 'create':
            dialog = BranchDialog(self, path, 'create')
            if dialog.exec_() == QDialog.Accepted:
                name = dialog.get_data()
                if not name:
                    self._show_warning(lang_mgr.get_text("buttons.ok"),
                                       lang_mgr.get_text("dialogs.create_branch.empty_name"))
                    return
                success, err = GitHelper.run_cmd(['checkout', '-b', name], path, self._log)
                if success:
                    self._log(lang_mgr.get_text("dialogs.create_branch.success").format(name), 'success')
                    self._refresh_branches()
                    self._load_branches_info()
                else:
                    self._log(lang_mgr.get_text("dialogs.create_branch.error").format(err), 'error')

        elif action == 'switch':
            dialog = BranchDialog(self, path, 'switch')
            if dialog.exec_() == QDialog.Accepted:
                branch = dialog.get_data()
                if not branch:
                    self._show_warning(lang_mgr.get_text("buttons.ok"),
                                       lang_mgr.get_text("dialogs.switch_branch.no_branch"))
                    return
                success, err = GitHelper.run_cmd(['checkout', branch], path, self._log)
                if success:
                    self._log(lang_mgr.get_text("dialogs.switch_branch.success").format(branch), 'success')
                    self._refresh_branches()
                    self._load_branches_info()
                else:
                    self._log(lang_mgr.get_text("dialogs.switch_branch.error").format(err), 'error')

        elif action == 'delete':
            current = GitHelper.get_current_branch(path)
            branches = [b for b in GitHelper.get_branches(path) if b != current]
            dialog = QDialog(self)
            dialog.setWindowTitle(lang_mgr.get_text("dialogs.delete_branch.title"))
            layout = QFormLayout(dialog)
            branch_combo = QComboBox()
            branch_combo.addItems(branches)
            layout.addRow(lang_mgr.get_text("dialogs.delete_branch.branch_label"), branch_combo)
            if current:
                layout.addRow(QLabel(lang_mgr.get_text("dialogs.delete_branch.current_warning").format(current)))
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addRow(buttons)
            if dialog.exec_() == QDialog.Accepted:
                branch = branch_combo.currentText()
                if branch == current:
                    self._show_warning(lang_mgr.get_text("buttons.ok"),
                                       lang_mgr.get_text("dialogs.delete_branch.cannot_delete_current"))
                    return
                reply = QMessageBox.question(self, lang_mgr.get_text("buttons.ok"),
                                             lang_mgr.get_text("dialogs.delete_branch.confirm").format(branch),
                                             QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    success, err = GitHelper.run_cmd(['branch', '-d', branch], path, self._log)
                    if success:
                        self._log(lang_mgr.get_text("dialogs.delete_branch.success").format(branch), 'success')
                        self._refresh_branches()
                        self._load_branches_info()
                    else:
                        self._log(lang_mgr.get_text("dialogs.delete_branch.error").format(err), 'error')

        elif action == 'merge':
            branches = GitHelper.get_branches(path)
            dialog = QDialog(self)
            dialog.setWindowTitle(lang_mgr.get_text("dialogs.merge_branches.title"))
            layout = QFormLayout(dialog)
            source_combo = QComboBox()
            target_combo = QComboBox()
            source_combo.addItems(branches)
            target_combo.addItems(branches)
            layout.addRow(lang_mgr.get_text("dialogs.merge_branches.source_label"), source_combo)
            layout.addRow(lang_mgr.get_text("dialogs.merge_branches.target_label"), target_combo)
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addRow(buttons)
            if dialog.exec_() == QDialog.Accepted:
                source = source_combo.currentText()
                target = target_combo.currentText()
                if not source or not target:
                    self._show_warning(lang_mgr.get_text("buttons.ok"), "Select both branches")
                    return
                if source == target:
                    self._show_warning(lang_mgr.get_text("buttons.ok"),
                                       lang_mgr.get_text("dialogs.merge_branches.same_branch"))
                    return
                reply = QMessageBox.question(self, lang_mgr.get_text("buttons.ok"),
                                             lang_mgr.get_text("dialogs.merge_branches.confirm").format(source, target),
                                             QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    success, err = GitHelper.merge_branch(path, source, target, self._log)
                    if success:
                        self._log(lang_mgr.get_text("dialogs.merge_branches.success").format(source, target), 'success')
                        self._refresh_branches()
                    else:
                        self._log(lang_mgr.get_text("dialogs.merge_branches.error").format(err), 'error')
                        self._show_warning(lang_mgr.get_text("buttons.ok"),
                                           lang_mgr.get_text("dialogs.merge_branches.conflict_warning"))

    def _switch_to_selected_branch(self):
        selected = self.branches_tree.selectedItems()
        if not selected:
            self._show_warning(lang_mgr.get_text("buttons.ok"),
                               lang_mgr.get_text("messages.select_branch_warning"))
            return
        branch = selected[0].text(0)
        path = self.branch_path.text().strip()
        success, err = GitHelper.run_cmd(['checkout', branch], path, self._log)
        if success:
            self._log(lang_mgr.get_text("dialogs.switch_branch.success").format(branch), 'success')
            self.current_branch_label.setText(f"  {branch}")
            self._load_branches_info()
            self._refresh_branches()
        else:
            self._log(lang_mgr.get_text("dialogs.switch_branch.error").format(err), 'error')

    def _delete_selected_branch(self):
        selected = self.branches_tree.selectedItems()
        if not selected:
            self._show_warning(lang_mgr.get_text("buttons.ok"),
                               lang_mgr.get_text("messages.select_branch_warning"))
            return
        branch = selected[0].text(0)
        path = self.branch_path.text().strip()
        current = GitHelper.get_current_branch(path)
        if branch == current:
            self._show_warning(lang_mgr.get_text("buttons.ok"),
                               lang_mgr.get_text("dialogs.delete_branch.cannot_delete_current"))
            return
        reply = QMessageBox.question(self, lang_mgr.get_text("buttons.ok"),
                                     lang_mgr.get_text("dialogs.delete_branch.confirm").format(branch),
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            success, err = GitHelper.run_cmd(['branch', '-d', branch], path, self._log)
            if success:
                self._log(lang_mgr.get_text("dialogs.delete_branch.success").format(branch), 'success')
                self._load_branches_info()
                self._refresh_branches()
            else:
                self._log(lang_mgr.get_text("dialogs.delete_branch.error").format(err), 'error')
