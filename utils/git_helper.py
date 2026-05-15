# utils/git_helper.py
import os
import subprocess
import re

class GitHelper:
    @staticmethod
    def is_git_installed():
        try:
            subprocess.run(['git', '--version'], capture_output=True, check=True)
            return True
        except: 
            return False

    @staticmethod
    def is_git_repo(path):
        return os.path.isdir(os.path.join(path, '.git'))

    @staticmethod
    def run_cmd(args, path, callback=None, extra_env=None):
        try:
            env = os.environ.copy()
            if extra_env: 
                env.update(extra_env)
            
            process = subprocess.Popen(
                ['git'] + args,
                cwd=path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
                encoding='utf-8',
                errors='replace'
            )
            
            for line in process.stdout:
                clean = re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', line).strip()
                if clean and callback: 
                    callback(clean)
            
            process.wait()
            return process.returncode == 0, ""
        except Exception as e:
            if callback: 
                callback(f"Error: {str(e)}")
            return False, str(e)

    @staticmethod
    def has_changes(path):
        """
        Надёжная проверка наличия изменений.
        Проверяет как изменённые, так и новые (неотслеживаемые) файлы.
        """
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            return bool(result.stdout.strip())
        except Exception as e:
            print(f"[WARNING] Error checking git status: {e}")
            return True

    @staticmethod
    def push(path, remote='origin', branch='main', token=None, callback=None, force=False):
        # Формируем команду push
        cmd = ['push']
        if force:
            cmd.append('--force')
        cmd.extend(['-u', remote, branch])
        
        if token:
            return GitHelper.run_cmd(
                cmd, path, callback,
                extra_env={'GIT_ASKPASS': 'echo', 'GIT_USERNAME': token, 'GIT_PASSWORD': 'x-oauth-basic'}
            )
        return GitHelper.run_cmd(cmd, path, callback)

    @staticmethod
    def get_branches(path):
        try:
            res = subprocess.run(['git', 'branch'], cwd=path, capture_output=True, text=True)
            return [line.strip().replace('*', '').strip() for line in res.stdout.splitlines() if line.strip()] or ['main']
        except: 
            return ['main']

    @staticmethod
    def get_current_branch(path):
        try:
            res = subprocess.run(['git', 'branch', '--show-current'], cwd=path, capture_output=True, text=True)
            return res.stdout.strip() or 'main'
        except: 
            return 'main'
            
    @staticmethod
    def get_last_commit(path, branch):
        try:
            res = subprocess.run(['git', 'log', '-1', '--oneline', branch], cwd=path, capture_output=True, text=True)
            return res.stdout.strip() or "N/A"
        except: 
            return "Error"