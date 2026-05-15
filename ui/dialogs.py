# ui/dialogs.py
from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox

from utils.lang_manager import lang_mgr

class BranchDialog(QDialog):
    def __init__(self, parent, path, action_type='create'):
        super().__init__(parent)
        self.path = path
        self.action_type = action_type
        self.setWindowTitle(lang_mgr.get_text(f"dialogs.{action_type}.title"))
        
        lay = QFormLayout(self)
        self.name_input = QLineEdit()
        lay.addRow(lang_mgr.get_text(f"dialogs.{action_type}.branch_name_label"), self.name_input)
        
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText(lang_mgr.get_text("buttons.ok"))
        btns.button(QDialogButtonBox.Cancel).setText(lang_mgr.get_text("buttons.cancel"))
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addRow(btns)

    def get_data(self):
        return self.name_input.text().strip()


class RepoDialog(QDialog):
    def __init__(self, parent, repo_data=None):
        super().__init__(parent)
        self.setWindowTitle(lang_mgr.get_text("dialogs.repo.title"))
        self.setMinimumWidth(400)
        
        lay = QFormLayout(self)
        
        self.name_inp = QLineEdit(repo_data.get('name', '') if repo_data else '')
        lay.addRow(lang_mgr.get_text("dialogs.repo.name"), self.name_inp)
        
        self.path_inp = QLineEdit(repo_data.get('path', '') if repo_data else '')
        lay.addRow(lang_mgr.get_text("deploy_tab.project_path_label"), self.path_inp)
        
        self.url_inp = QLineEdit(repo_data.get('url', '') if repo_data else '')
        lay.addRow(lang_mgr.get_text("deploy_tab.repo_url_label"), self.url_inp)
        
        self.branch_inp = QLineEdit(repo_data.get('branch', 'main') if repo_data else 'main')
        lay.addRow(lang_mgr.get_text("deploy_tab.branch_label"), self.branch_inp)
        
        self.token_inp = QLineEdit(repo_data.get('token', '') if repo_data else '')
        self.token_inp.setEchoMode(QLineEdit.Password)
        lay.addRow(lang_mgr.get_text("deploy_tab.token_group"), self.token_inp)
        
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText(lang_mgr.get_text("buttons.ok"))
        btns.button(QDialogButtonBox.Cancel).setText(lang_mgr.get_text("buttons.cancel"))
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addRow(btns)
        
    def get_data(self):
        return {
            'name': self.name_inp.text().strip(),
            'path': self.path_inp.text().strip(),
            'url': self.url_inp.text().strip(),
            'branch': self.branch_inp.text().strip() or 'main',
            'token': self.token_inp.text().strip()
        }