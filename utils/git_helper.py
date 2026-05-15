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
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                encoding='utf-8',
                errors='replace'
            )
            
            output_lines = []
            for line in process.stdout:
                clean = re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', line).strip()
                if clean and callback: 
                    callback(clean)
                output_lines.append(clean)
            
            stderr = process.stderr.read()
            if stderr and callback:
                callback(f"ERROR: {stderr.strip()}")
            
            process.wait()
            
            if process.returncode != 0:
                error_msg = stderr.strip() or "Unknown git error"
                if callback:
                    callback(f"❌ Git command failed: {error_msg}")
                return False, error_msg
                
            return True, ""
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
    def scan_for_secrets(path, callback=None):
        """
        Сканирует отслеживаемые файлы на наличие потенциальных секретов.
        Возвращает список найденных проблем: [(файл, строка, тип_секрета), ...]
        """
        # Паттерны для распространённых секретов
        SECRET_PATTERNS = {
            'GitHub PAT (Classic)': r'ghp_[A-Za-z0-9]{36,}',
            'GitHub PAT (Fine-grained)': r'github_pat_[A-Za-z0-9]{22,}_[A-Za-z0-9]{59}',
            'GitHub OAuth': r'gho_[A-Za-z0-9]{36,}',
            'GitHub App Token': r'ghs_[A-Za-z0-9]{36,}',
            'Generic API Key': r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?[A-Za-z0-9_\-]{20,}',
            'Password in URL': r'https?://[^:]+:[^@]+@',
            'AWS Access Key': r'AKIA[0-9A-Z]{16}',
        }
        
        # Файлы, которые ВСЕГДА игнорируем (даже если в индексе)
        AUTO_EXCLUDE = {
            'repositories.json',
            'secure_token.dat', 
            '*.env',
            'config_local.py',
            'secrets.json',
            '.env.local',
            '*.key',
            '*.pem'
        }
        
        findings = []
        
        try:
            # Получаем список отслеживаемых файлов
            res = subprocess.run(
                ['git', 'ls-files', '--cached'],
                cwd=path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            for file_path in res.stdout.strip().splitlines():
                if not file_path:
                    continue
                    
                # Пропускаем файлы из авто-исключения
                if any(file_path == exc or file_path.endswith(exc.replace('*', '')) for exc in AUTO_EXCLUDE):
                    if callback:
                        callback(f"🔒 Исключён из проверки: {file_path}")
                    continue
                
                full_path = os.path.join(path, file_path)
                if not os.path.isfile(full_path):
                    continue
                    
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f, 1):
                            for secret_name, pattern in SECRET_PATTERNS.items():
                                if re.search(pattern, line):
                                    findings.append((file_path, line_num, secret_name))
                                    if callback:
                                        callback(f"⚠️ Секрет '{secret_name}' в {file_path}:{line_num}")
                except Exception:
                    pass  # Пропускаем файлы, которые не удалось прочитать
                    
        except Exception as e:
            if callback:
                callback(f"[WARNING] Secret scan error: {e}")
                
        return findings

    @staticmethod
    def auto_fix_ignored_files(path, callback=None):
        """
        Автоматически удаляет из индекса файлы, которые есть в .gitignore,
        но всё ещё отслеживаются Git.
        """
        try:
            # Получаем список файлов, которые игнорируются, но отслеживаются
            res = subprocess.run(
                ['git', 'ls-files', '--ignored', '--exclude-standard'],
                cwd=path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            fixed = []
            for file_path in res.stdout.strip().splitlines():
                if file_path:
                    # Удаляем из индекса, но оставляем на диске
                    subprocess.run(
                        ['git', 'rm', '--cached', file_path],
                        cwd=path,
                        capture_output=True,
                        text=True
                    )
                    fixed.append(file_path)
                    if callback:
                        callback(f"🔒 Auto-fix: удалён из индекса: {file_path}")
            
            return fixed
        except Exception as e:
            if callback:
                callback(f"[WARNING] Auto-fix error: {e}")
            return []

    @staticmethod
    def is_remote_empty(path, remote='origin', branch='main', callback=None):
        """
        Проверяет, пуст ли удалённый репозиторий (нет коммитов в ветке).
        Возвращает True, если ветка не существует на сервере.
        """
        try:
            res = subprocess.run(
                ['git', 'ls-remote', '--heads', remote, branch],
                cwd=path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            # Если вывод пустой — ветка не существует на сервере (пустой репо)
            return not res.stdout.strip()
        except Exception:
            return False  # При ошибке считаем, что не пустой (безопаснее)

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