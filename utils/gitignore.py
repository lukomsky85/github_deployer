# utils/gitignore.py
import os
from config import DEFAULT_GITIGNORE

class GitignoreManager:
    @staticmethod
    def get_path(project_path):
        return os.path.join(project_path, '.gitignore')
    
    @staticmethod
    def load(project_path):
        path = GitignoreManager.get_path(project_path)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                return DEFAULT_GITIGNORE
        return DEFAULT_GITIGNORE
    
    @staticmethod
    def save(project_path, content):
        path = GitignoreManager.get_path(project_path)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, "Saved"
        except Exception as e:
            return False, str(e)