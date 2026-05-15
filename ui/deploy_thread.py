# ui/deploy_thread.py
import os
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal

from utils.git_helper import GitHelper
from utils.history import CommitHistoryManager
from config import DEFAULT_GITIGNORE
from utils.lang_manager import lang_mgr

class DeployThread(QThread):
    # Сигналы для общения с UI
    log_signal = pyqtSignal(str, str)      # (message, level)
    finished_signal = pyqtSignal(bool, str) # (success, details)
    
    def __init__(self, path, repo, token, message, do_gitignore, branch, create_branch, do_pull=False):
        super().__init__()
        self.path = path
        self.repo = repo
        self.token = token
        self.message = message
        self.do_gitignore = do_gitignore
        self.branch = branch
        self.create_branch = create_branch
        self.do_pull = do_pull
    
    def log(self, msg, level='info'):
        """Отправляет сообщение и уровень в UI. Иконки добавляются на стороне интерфейса."""
        self.log_signal.emit(msg, level)
    
    def run(self):
        try:
            self.log(f"Start: {self.path}", 'info')
            
            # ── Инициализация репозитория ─────────────────────────────
            if not GitHelper.is_git_repo(self.path):
                self.log("Initializing repository...", 'info')
                GitHelper.run_cmd(['init'], self.path, self.log)
                GitHelper.run_cmd(['branch', '-M', 'main'], self.path, self.log)

            # ── Создание .gitignore ───────────────────────────────────
            if self.do_gitignore:
                gi_path = os.path.join(self.path, '.gitignore')
                if not os.path.exists(gi_path):
                    with open(gi_path, 'w', encoding='utf-8') as f:
                        f.write(DEFAULT_GITIGNORE)
                    self.log("Created .gitignore", 'success')

            # ── 🔧 AUTO-FIX: Удаляем из индекса файлы из .gitignore ───
            self.log("Checking index for ignored files...", 'info')
            fixed_files = GitHelper.auto_fix_ignored_files(self.path, callback=self.log)
            if fixed_files:
                self.log(f"Auto-fixed {len(fixed_files)} files in index", 'success')

            # ── Настройка remote origin ───────────────────────────────
            GitHelper.run_cmd(['remote', 'remove', 'origin'], self.path, self.log)
            GitHelper.run_cmd(['remote', 'add', 'origin', self.repo], self.path, self.log)

            # ── Переключение/создание ветки ───────────────────────────
            current = GitHelper.get_current_branch(self.path)
            if self.create_branch:
                self.log(f"Creating branch: {self.branch}", 'info')
                GitHelper.run_cmd(['checkout', '-b', self.branch], self.path, self.log)
            elif current != self.branch:
                self.log(f"Switching to branch: {self.branch}", 'info')
                ok, _ = GitHelper.run_cmd(['checkout', self.branch], self.path, self.log)
                if not ok:
                    GitHelper.run_cmd(['checkout', '-b', self.branch], self.path, self.log)

            # ── Fetch + Pull (опционально) ────────────────────────────
            self.log("Fetching remote updates...", 'info')
            GitHelper.run_cmd(['fetch', 'origin'], self.path, self.log)
            
            if self.do_pull:
                self.log("Syncing with remote (pull --rebase)...", 'info')
                ok, err = GitHelper.run_cmd(['pull', '--rebase', 'origin', self.branch], self.path, self.log)
                if not ok:
                    self.log("Auto-sync failed. Proceeding with local state.", 'warning')
            
            # ── Staging ───────────────────────────────────────────────
            self.log("Staging changes (git add -A)...", 'info')
            GitHelper.run_cmd(['add', '-A'], self.path, self.log)

            # ── Commit (только если есть изменения) ───────────────────
            if GitHelper.has_changes(self.path):
                commit_msg = self.message if self.message else f"Update {datetime.now().strftime('%H:%M')}"
                self.log(f"Committing: '{commit_msg}'", 'info')
                GitHelper.run_cmd(['config', 'user.email', 'helper@local'], self.path, self.log)
                GitHelper.run_cmd(['config', 'user.name', 'Deploy Helper'], self.path, self.log)
                
                ok, err = GitHelper.run_cmd(['commit', '-m', commit_msg], self.path, self.log)
                if not ok: 
                    raise Exception(err)
                
                if self.message: 
                    CommitHistoryManager.save_message(self.message)
            else:
                self.log(lang_mgr.get_text("messages.no_changes"), 'info')

            # ── 🔐 ПРОВЕРКА НА СЕКРЕТЫ ────────────────────────────────
            self.log("Scanning for secrets...", 'info')
            secrets = GitHelper.scan_for_secrets(self.path, callback=self.log)
            
            if secrets:
                self.log(lang_mgr.get_text("messages.secrets_found"), 'error')
                self.log(lang_mgr.get_text("messages.secrets_advice"), 'warning')
                
                secret_files = list(set(f for f, _, _ in secrets))
                error_msg = f"Secrets detected: {', '.join(secret_files)}"
                self.finished_signal.emit(False, error_msg)
                return
            
            self.log(lang_mgr.get_text("messages.secrets_clean"), 'success')

            # ── 🚀 PUSH (ВСЕГДА С --force) ───────────────────────────
            self.log(f"Pushing to {self.branch}...", 'info')
            success, err = GitHelper.push(
                self.path, 
                branch=self.branch, 
                token=self.token, 
                callback=self.log,
                force=True  # Принудительная отправка
            )
            
            # ── Обработка результата ──────────────────────────────────
            if success:
                branch_upper = self.branch.upper()
                self.log(lang_mgr.get_text("messages.deploy_success").format(branch=branch_upper), 'success')
                self.finished_signal.emit(True, lang_mgr.get_text("messages.deploy_success_message").format(branch=self.branch))
            else:
                if "rejected" in err.lower():
                    if "GH013" in err or "secret" in err.lower():
                        self.log(lang_mgr.get_text("messages.secret_in_history"), 'error')
                        self.log(lang_mgr.get_text("messages.secret_allow_hint"), 'warning')
                    self.log(lang_mgr.get_text("messages.push_rejected"), 'error')
                    self.finished_signal.emit(False, "Rejected")
                elif "auth" in err.lower() or "403" in err:
                    self.log(lang_mgr.get_text("messages.auth_error"), 'error')
                    self.finished_signal.emit(False, "Auth Failed")
                else:
                    self.log(lang_mgr.get_text("messages.push_error").format(error=err), 'error')
                    self.finished_signal.emit(False, err)

        except Exception as e:
            self.log(lang_mgr.get_text("messages.critical_error").format(error=str(e)), 'error')
            self.finished_signal.emit(False, str(e))