# utils/scheduler.py
"""
Планировщик автодеплоя — запускает деплой по расписанию.
Работает в фоновом QThread, не блокирует UI.
"""
import os
import json
from datetime import datetime, time
from PyQt5.QtCore import QThread, pyqtSignal, QTimer


SCHEDULES_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'schedules.json'
)


class ScheduleEntry:
    """Одна запись расписания."""

    INTERVALS = {
        'every_30min':  30,
        'every_hour':   60,
        'every_2h':     120,
        'every_6h':     360,
        'every_12h':    720,
        'every_day':    1440,
    }

    def __init__(self, data: dict):
        self.id          = data.get('id', '')
        self.name        = data.get('name', '')
        self.enabled     = data.get('enabled', False)
        self.repo_name   = data.get('repo_name', '')   # имя профиля репозитория
        self.interval    = data.get('interval', 'every_hour')  # ключ из INTERVALS
        self.commit_msg  = data.get('commit_msg', 'Auto-deploy')
        self.branch      = data.get('branch', 'main')
        self.run_pre     = data.get('run_pre', True)   # запускать pre-хуки
        self.run_post    = data.get('run_post', True)  # запускать post-хуки
        # Когда последний раз запускали (ISO строка)
        self.last_run    = data.get('last_run', None)
        self.last_status = data.get('last_status', '')  # 'success' | 'error' | ''
        self.next_run    = data.get('next_run', None)

    def to_dict(self) -> dict:
        return {
            'id':          self.id,
            'name':        self.name,
            'enabled':     self.enabled,
            'repo_name':   self.repo_name,
            'interval':    self.interval,
            'commit_msg':  self.commit_msg,
            'branch':      self.branch,
            'run_pre':     self.run_pre,
            'run_post':    self.run_post,
            'last_run':    self.last_run,
            'last_status': self.last_status,
            'next_run':    self.next_run,
        }

    def interval_minutes(self) -> int:
        return self.INTERVALS.get(self.interval, 60)

    def is_due(self) -> bool:
        """Пора ли запускать деплой?"""
        if not self.enabled:
            return False
        if not self.last_run:
            return True
        try:
            last = datetime.fromisoformat(self.last_run)
            elapsed = (datetime.now() - last).total_seconds() / 60
            return elapsed >= self.interval_minutes()
        except Exception:
            return True

    def mark_run(self, success: bool):
        self.last_run    = datetime.now().isoformat()
        self.last_status = 'success' if success else 'error'
        mins = self.interval_minutes()
        from datetime import timedelta
        self.next_run = (datetime.now() + timedelta(minutes=mins)).isoformat()


class ScheduleManager:
    """Загрузка/сохранение расписаний."""

    @staticmethod
    def load() -> list:
        try:
            data = json.load(open(SCHEDULES_FILE, encoding='utf-8'))
            return [ScheduleEntry(d) for d in data]
        except Exception:
            return []

    @staticmethod
    def save(entries: list):
        try:
            json.dump(
                [e.to_dict() for e in entries],
                open(SCHEDULES_FILE, 'w', encoding='utf-8'),
                ensure_ascii=False, indent=4
            )
        except Exception as e:
            print(f"[scheduler] save failed: {e}")

    @staticmethod
    def new_id() -> str:
        import uuid
        return str(uuid.uuid4())[:8]


class SchedulerThread(QThread):
    """
    Тикает каждую минуту, проверяет расписания,
    эмитирует сигнал когда пора деплоить.
    """
    deploy_due  = pyqtSignal(object)        # ScheduleEntry
    tick        = pyqtSignal(str)           # текущее время строкой
    status_changed = pyqtSignal(object, bool)  # entry, success

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = True
        self.entries: list = []

    def stop(self):
        self._running = False

    def reload(self):
        self.entries = ScheduleManager.load()

    def run(self):
        self.entries = ScheduleManager.load()
        timer_count = 0

        while self._running:
            self.msleep(10_000)   # проверяем каждые 10 секунд
            if not self._running:
                break

            now_str = datetime.now().strftime('%H:%M:%S')
            self.tick.emit(now_str)

            for entry in self.entries:
                if entry.is_due():
                    self.deploy_due.emit(entry)
