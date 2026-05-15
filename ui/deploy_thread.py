# ui/deploy_thread.py
import os
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal

from utils.git_helper import GitHelper
from utils.history import CommitHistoryManager
from config import DEFAULT_GITIGNORE
from utils.lang_manager import lang_mgr

class DeployThread(QThread):
    log_signal = pyqtSignal(str, str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, path, repo, token, message, do_gitignore, branch, create_branch):
        super().__init__()
        self.path = path
        self.repo = repo
        self.token = token
        self.message = message
        self.do_gitignore = do_gitignore
        self.branch = branch
        self.create_branch = create_branch
    
    def log(self, msg, level='info'):
        self.log_signal.emit(msg, level)
    
    def run(self):
        try:
            self.log(f"🎯 Start: {self.path}")
            
            if not GitHelper.is_git_repo(self.path):
                self.log("🔄 Init repo...")
                GitHelper.run_cmd(['init'], self.path, self.log)
                GitHelper.run_cmd(['branch', '-M', 'main'], self.path, self.log)

            if self.do_gitignore:
                gi_path = os.path.join(self.path, '.gitignore')
                if not os.path.exists(gi_path):
                    with open(gi_path, 'w', encoding='utf-8') as f:
                        f.write(DEFAULT_GITIGNORE)
                    self.log("✅ Created .gitignore", 'success')

            GitHelper.run_cmd(['remote', 'remove', 'origin'], self.path, self.log)
            GitHelper.run_cmd(['remote', 'add', 'origin', self.repo], self.path, self.log)

            current = GitHelper.get_current_branch(self.path)
            if self.create_branch:
                self.log(f"🌿 Create: {self.branch}")
                GitHelper.run_cmd(['checkout', '-b', self.branch], self.path, self.log)
            elif current != self.branch:
                self.log(f"🌿 Checkout: {self.branch}")
                ok, _ = GitHelper.run_cmd(['checkout', self.branch], self.path, self.log)
                if not ok:
                    GitHelper.run_cmd(['checkout', '-b', self.branch], self.path, self.log)

            self.log("📥 Fetching...")
            GitHelper.run_cmd(['fetch', 'origin'], self.path, self.log)
            
            self.log("📦 Staging (git add -A)...")
            GitHelper.run_cmd(['add', '-A'], self.path, self.log)

            # ✅ Коммитим только если есть изменения
            if GitHelper.has_changes(self.path):
                msg = self.message if self.message else f"🔄 Update {datetime.now().strftime('%H:%M')}"
                self.log(f"💾 Commit: '{msg}'")
                GitHelper.run_cmd(['config', 'user.email', 'helper@local'], self.path, self.log)
                GitHelper.run_cmd(['config', 'user.name', 'Deploy Helper'], self.path, self.log)
                
                ok, err = GitHelper.run_cmd(['commit', '-m', msg], self.path, self.log)
                if not ok: 
                    raise Exception(err)
                
                if self.message: 
                    CommitHistoryManager.save_message(self.message)
            else:
                self.log("✨ Локальные изменения отсутствуют (коммит пропущен)", 'info')

            # 🔐 ПРОВЕРКА НА СЕКРЕТЫ ПЕРЕД ПУШЕМ
            self.log("🔍 Сканирование на секреты...")
            secrets = GitHelper.scan_for_secrets(self.path, callback=self.log)
            
            if secrets:
                self.log(f"❌ Обнаружено {len(secrets)} потенциальных секретов!", 'error')
                self.log("💡 Совет: добавьте файлы с токенами в .gitignore", 'warning')
                
                # Формируем понятное сообщение об ошибке
                secret_files = list(set(f for f, _, _ in secrets))
                error_msg = f"Secrets detected: {', '.join(secret_files)}"
                self.finished_signal.emit(False, error_msg)
                return  # ⛔ Останавливаем пуш!
            
            self.log("✨ Секреты не обнаружены — продолжаем", 'success')

            # 🚀 ПУШ ВЫПОЛНЯЕТСЯ ВСЕГДА (даже если нет новых коммитов)
            self.log(f"🚀 Pushing to {self.branch}...")
            success, err = GitHelper.push(
                self.path, 
                branch=self.branch, 
                token=self.token, 
                callback=self.log,
                force=True
            )
            
            if success:
                branch_upper = self.branch.upper()
                self.log(lang_mgr.get_text("messages.deploy_success", branch=branch_upper), 'success')
                self.finished_signal.emit(True, lang_mgr.get_text("messages.deploy_success_message", branch=self.branch))
            else:
                if "rejected" in err.lower():
                    self.log(lang_mgr.get_text("messages.push_rejected"), 'error')
                    self.finished_signal.emit(False, "Rejected")
                elif "auth" in err.lower() or "403" in err:
                    self.log(lang_mgr.get_text("messages.auth_error"), 'error')
                    self.finished_signal.emit(False, "Auth Failed")
                else:
                    self.log(lang_mgr.get_text("messages.push_error", error=err), 'error')
                    self.finished_signal.emit(False, err)

        except Exception as e:
            self.log(lang_mgr.get_text("messages.critical_error", error=str(e)), 'error')
            self.finished_signal.emit(False, str(e))