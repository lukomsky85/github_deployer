# utils/history.py
import os
import json

class CommitHistoryManager:
    HISTORY_FILE = "commit_history.json"
    MAX_HISTORY = 20

    @staticmethod
    def load_history():
        if not os.path.exists(CommitHistoryManager.HISTORY_FILE):
            return ["🚀 Initial commit", "✨ Update", "🐛 Fix"]
        try:
            with open(CommitHistoryManager.HISTORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except:
            return []

    @staticmethod
    def save_message(message):
        if not message: 
            return
        history = CommitHistoryManager.load_history()
        if message in history: 
            history.remove(message)
        history.insert(0, message)
        with open(CommitHistoryManager.HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history[:CommitHistoryManager.MAX_HISTORY], f, ensure_ascii=False, indent=2)