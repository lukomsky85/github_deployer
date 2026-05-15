# utils/repo_manager.py
import os
import json

class RepositoryManager:
    FILE = "repositories.json"
    
    def __init__(self):
        self.repos = self._load()
        
    def _load(self):
        if not os.path.exists(self.FILE):
            return []
        try:
            with open(self.FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except:
            return []
            
    def save(self):
        with open(self.FILE, 'w', encoding='utf-8') as f:
            json.dump(self.repos, f, ensure_ascii=False, indent=2)
            
    def add(self, repo):
        self.repos.append(repo)
        self.save()
        
    def update(self, index, repo):
        if 0 <= index < len(self.repos):
            self.repos[index] = repo
            self.save()
            
    def delete(self, index):
        if 0 <= index < len(self.repos):
            del self.repos[index]
            self.save()
            
    def get_all_names(self):
        return [r.get('name', f'Repo {i+1}') for i, r in enumerate(self.repos)]
        
    def get(self, index):
        return self.repos[index] if 0 <= index < len(self.repos) else None