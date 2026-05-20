# ui/automation_tab.py
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QSplitter, QFrame, QTextEdit, QLineEdit,
    QComboBox, QCheckBox, QSpinBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QDialog, QFormLayout,
    QDialogButtonBox, QSizePolicy, QScrollArea
)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QFont, QColor

from utils.lang_manager import lang_mgr
from utils.icon_manager import IconManager
from utils.hooks import HooksManager, Hook
from utils.scheduler import ScheduleManager, ScheduleEntry, SchedulerThread


# ── Диалог редактирования хука ────────────────────────────────────────────────

class HookDialog(QDialog):
    def __init__(self, parent=None, hook: Hook = None):
        super().__init__(parent)
        self.setWindowTitle(lang_mgr.get_text("automation.hook_dialog_title"))
        self.setMinimumWidth(480)
        self._hook = hook
        self._build()

    def _build(self):
        lay = QFormLayout(self)
        lay.setSpacing(10)

        self._name = QLineEdit(self._hook.name if self._hook else '')
        self._name.setPlaceholderText(lang_mgr.get_text("automation.hook_name_placeholder"))
        lay.addRow(lang_mgr.get_text("automation.hook_name"), self._name)

        self._type = QComboBox()
        self._type.addItem(lang_mgr.get_text("automation.hook_type_pre"),  'pre')
        self._type.addItem(lang_mgr.get_text("automation.hook_type_post"), 'post')
        if self._hook:
            self._type.setCurrentIndex(0 if self._hook.type == 'pre' else 1)
        lay.addRow(lang_mgr.get_text("automation.hook_type"), self._type)

        self._cmd = QLineEdit(self._hook.command if self._hook else '')
        self._cmd.setPlaceholderText("python test.py  /  npm run build  /  ./deploy.sh")
        lay.addRow(lang_mgr.get_text("automation.hook_command"), self._cmd)

        self._timeout = QSpinBox()
        self._timeout.setRange(5, 3600)
        self._timeout.setValue(self._hook.timeout if self._hook else 60)
        self._timeout.setSuffix(" " + lang_mgr.get_text("automation.seconds"))
        lay.addRow(lang_mgr.get_text("automation.hook_timeout"), self._timeout)

        self._stop_on_fail = QCheckBox(lang_mgr.get_text("automation.hook_stop_on_fail"))
        self._stop_on_fail.setChecked(self._hook.stop_on_fail if self._hook else True)
        lay.addRow('', self._stop_on_fail)

        self._enabled = QCheckBox(lang_mgr.get_text("automation.hook_enabled"))
        self._enabled.setChecked(self._hook.enabled if self._hook else True)
        lay.addRow('', self._enabled)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addRow(btns)

    def get_data(self) -> dict:
        return {
            'name':         self._name.text().strip(),
            'type':         self._type.currentData(),
            'command':      self._cmd.text().strip(),
            'timeout':      self._timeout.value(),
            'stop_on_fail': self._stop_on_fail.isChecked(),
            'enabled':      self._enabled.isChecked(),
        }


# ── Диалог редактирования расписания ─────────────────────────────────────────

class ScheduleDialog(QDialog):
    def __init__(self, parent=None, entry: ScheduleEntry = None, repo_names=None):
        super().__init__(parent)
        self.setWindowTitle(lang_mgr.get_text("automation.schedule_dialog_title"))
        self.setMinimumWidth(420)
        self._entry = entry
        self._repo_names = repo_names or []
        self._build()

    def _build(self):
        lay = QFormLayout(self)
        lay.setSpacing(10)

        self._name = QLineEdit(self._entry.name if self._entry else '')
        self._name.setPlaceholderText(lang_mgr.get_text("automation.schedule_name_placeholder"))
        lay.addRow(lang_mgr.get_text("automation.schedule_name"), self._name)

        self._repo = QComboBox()
        self._repo.addItems(self._repo_names or [lang_mgr.get_text("automation.no_profiles")])
        if self._entry and self._entry.repo_name in self._repo_names:
            self._repo.setCurrentText(self._entry.repo_name)
        lay.addRow(lang_mgr.get_text("automation.schedule_repo"), self._repo)

        self._interval = QComboBox()
        intervals = [
            ('every_30min', lang_mgr.get_text("automation.interval_30min")),
            ('every_hour',  lang_mgr.get_text("automation.interval_1h")),
            ('every_2h',    lang_mgr.get_text("automation.interval_2h")),
            ('every_6h',    lang_mgr.get_text("automation.interval_6h")),
            ('every_12h',   lang_mgr.get_text("automation.interval_12h")),
            ('every_day',   lang_mgr.get_text("automation.interval_24h")),
        ]
        for key, label in intervals:
            self._interval.addItem(label, key)
        if self._entry:
            for i in range(self._interval.count()):
                if self._interval.itemData(i) == self._entry.interval:
                    self._interval.setCurrentIndex(i)
        lay.addRow(lang_mgr.get_text("automation.schedule_interval"), self._interval)

        self._commit = QLineEdit(self._entry.commit_msg if self._entry else 'Auto-deploy')
        lay.addRow(lang_mgr.get_text("automation.schedule_commit"), self._commit)

        self._branch = QLineEdit(self._entry.branch if self._entry else 'main')
        lay.addRow(lang_mgr.get_text("automation.schedule_branch"), self._branch)

        self._run_pre  = QCheckBox(lang_mgr.get_text("automation.schedule_run_pre"))
        self._run_pre.setChecked(self._entry.run_pre if self._entry else True)
        lay.addRow('', self._run_pre)

        self._run_post = QCheckBox(lang_mgr.get_text("automation.schedule_run_post"))
        self._run_post.setChecked(self._entry.run_post if self._entry else True)
        lay.addRow('', self._run_post)

        self._enabled = QCheckBox(lang_mgr.get_text("automation.schedule_enabled"))
        self._enabled.setChecked(self._entry.enabled if self._entry else True)
        lay.addRow('', self._enabled)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addRow(btns)

    def get_data(self) -> dict:
        return {
            'name':      self._name.text().strip(),
            'repo_name': self._repo.currentText(),
            'interval':  self._interval.currentData(),
            'commit_msg':self._commit.text().strip() or 'Auto-deploy',
            'branch':    self._branch.text().strip() or 'main',
            'run_pre':   self._run_pre.isChecked(),
            'run_post':  self._run_post.isChecked(),
            'enabled':   self._enabled.isChecked(),
        }


# ── Вкладка Автоматизация ─────────────────────────────────────────────────────

class AutomationTabMixin:

    def _create_automation_tab(self):
        self._hooks:   list = HooksManager.load()
        self._schedules: list = ScheduleManager.load()
        self._scheduler_thread = None
        icons = IconManager()

        tab = QWidget()
        root = QVBoxLayout(tab)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter)

        # ══ ЛЕВАЯ ПАНЕЛЬ — Хуки ════════════════════════════════════════
        left = QWidget()
        left.setMinimumWidth(400)
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(12, 12, 6, 12)
        left_lay.setSpacing(8)

        # Заголовок хуков
        hdr = QHBoxLayout()
        hdr_lbl = QLabel(lang_mgr.get_text("automation.hooks_title"))
        hdr_lbl.setStyleSheet("font-size: 12pt; font-weight: 700; color: #4c4f69;")
        hdr.addWidget(hdr_lbl)
        hdr.addStretch()
        sub = QLabel(lang_mgr.get_text("automation.hooks_subtitle"))
        sub.setStyleSheet("font-size: 9pt; color: #8c8fa1;")
        hdr.addWidget(sub)
        left_lay.addLayout(hdr)

        # Кнопки управления хуками
        hook_btns = QHBoxLayout()
        hook_btns.setSpacing(6)

        btn_add_hook = QPushButton(lang_mgr.get_text("automation.add_hook"))
        btn_add_hook.setStyleSheet(
            "QPushButton { background:#e8f0fe; color:#1e66f5; border:1px solid #b8d0fb;"
            " border-radius:7px; padding:6px 12px; font-weight:500; }"
            "QPushButton:hover { background:#d0e4fd; }"
        )
        icons.set_button_icon(btn_add_hook, 'add', color='#1e66f5', size=QSize(14, 14))
        btn_add_hook.clicked.connect(self._hook_add)
        hook_btns.addWidget(btn_add_hook)

        btn_edit_hook = QPushButton(lang_mgr.get_text("automation.edit_hook"))
        icons.set_button_icon(btn_edit_hook, 'edit', size=QSize(14, 14))
        btn_edit_hook.clicked.connect(self._hook_edit)
        hook_btns.addWidget(btn_edit_hook)

        btn_del_hook = QPushButton(lang_mgr.get_text("automation.delete_hook"))
        btn_del_hook.setStyleSheet(
            "QPushButton { color:#d20f39; }"
            "QPushButton:hover { border-color:#fca5a5; background:#fff1f2; }"
        )
        icons.set_danger_button_icon(btn_del_hook, 'delete', size=QSize(14, 14))
        btn_del_hook.clicked.connect(self._hook_delete)
        hook_btns.addWidget(btn_del_hook)
        hook_btns.addStretch()

        btn_run_pre = QPushButton(lang_mgr.get_text("automation.run_pre_now"))
        btn_run_pre.setStyleSheet(
            "QPushButton { background:#f0fdf4; color:#40a02b; border:1px solid #86efac;"
            " border-radius:7px; padding:6px 12px; }"
            "QPushButton:hover { background:#dcfce7; }"
        )
        btn_run_pre.clicked.connect(lambda: self._run_hooks_now('pre'))
        hook_btns.addWidget(btn_run_pre)

        btn_run_post = QPushButton(lang_mgr.get_text("automation.run_post_now"))
        btn_run_post.setStyleSheet(
            "QPushButton { background:#f0fdf4; color:#40a02b; border:1px solid #86efac;"
            " border-radius:7px; padding:6px 12px; }"
            "QPushButton:hover { background:#dcfce7; }"
        )
        btn_run_post.clicked.connect(lambda: self._run_hooks_now('post'))
        hook_btns.addWidget(btn_run_post)

        left_lay.addLayout(hook_btns)

        # Таблица хуков
        self._hooks_table = QTableWidget(0, 5)
        self._hooks_table.setHorizontalHeaderLabels([
            lang_mgr.get_text("automation.col_enabled"),
            lang_mgr.get_text("automation.col_type"),
            lang_mgr.get_text("automation.col_name"),
            lang_mgr.get_text("automation.col_command"),
            lang_mgr.get_text("automation.col_last"),
        ])
        self._hooks_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self._hooks_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._hooks_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._hooks_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._hooks_table.setAlternatingRowColors(True)
        self._hooks_table.verticalHeader().setVisible(False)
        self._hooks_table.setColumnWidth(0, 60)
        self._hooks_table.setColumnWidth(1, 60)
        left_lay.addWidget(self._hooks_table, 1)

        # Лог хуков
        hooks_log_group = QGroupBox(lang_mgr.get_text("automation.hooks_log"))
        hooks_log_lay = QVBoxLayout(hooks_log_group)
        self._hooks_log = QTextEdit()
        self._hooks_log.setReadOnly(True)
        self._hooks_log.setFont(QFont("Consolas", 9))
        self._hooks_log.setMaximumHeight(120)
        self._hooks_log.setStyleSheet(
            "QTextEdit { background:#f8f9fc; border:1px solid #dce0e8;"
            " border-radius:7px; padding:6px; }"
        )
        hooks_log_lay.addWidget(self._hooks_log)
        left_lay.addWidget(hooks_log_group)

        splitter.addWidget(left)

        # ══ ПРАВАЯ ПАНЕЛЬ — Расписание ══════════════════════════════════
        right = QWidget()
        right.setMinimumWidth(420)
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(6, 12, 12, 12)
        right_lay.setSpacing(8)

        # Заголовок расписания
        shdr = QHBoxLayout()
        shdr_lbl = QLabel(lang_mgr.get_text("automation.schedule_title"))
        shdr_lbl.setStyleSheet("font-size: 12pt; font-weight: 700; color: #4c4f69;")
        shdr.addWidget(shdr_lbl)
        shdr.addStretch()

        # Статус планировщика
        self._scheduler_status = QLabel(lang_mgr.get_text("automation.scheduler_stopped"))
        self._scheduler_status.setStyleSheet("font-size: 9pt; color: #d20f39; font-weight: 600;")
        shdr.addWidget(self._scheduler_status)
        right_lay.addLayout(shdr)

        # Кнопки управления расписанием
        sched_btns = QHBoxLayout()
        sched_btns.setSpacing(6)

        btn_add_sched = QPushButton(lang_mgr.get_text("automation.add_schedule"))
        btn_add_sched.setStyleSheet(
            "QPushButton { background:#e8f0fe; color:#1e66f5; border:1px solid #b8d0fb;"
            " border-radius:7px; padding:6px 12px; font-weight:500; }"
            "QPushButton:hover { background:#d0e4fd; }"
        )
        icons.set_button_icon(btn_add_sched, 'add', color='#1e66f5', size=QSize(14, 14))
        btn_add_sched.clicked.connect(self._sched_add)
        sched_btns.addWidget(btn_add_sched)

        btn_edit_sched = QPushButton(lang_mgr.get_text("automation.edit_schedule"))
        icons.set_button_icon(btn_edit_sched, 'edit', size=QSize(14, 14))
        btn_edit_sched.clicked.connect(self._sched_edit)
        sched_btns.addWidget(btn_edit_sched)

        btn_del_sched = QPushButton(lang_mgr.get_text("automation.delete_schedule"))
        btn_del_sched.setStyleSheet(
            "QPushButton { color:#d20f39; }"
            "QPushButton:hover { border-color:#fca5a5; background:#fff1f2; }"
        )
        icons.set_danger_button_icon(btn_del_sched, 'delete', size=QSize(14, 14))
        btn_del_sched.clicked.connect(self._sched_delete)
        sched_btns.addWidget(btn_del_sched)

        sched_btns.addStretch()

        # Кнопка запуска/остановки планировщика
        self._btn_start_scheduler = QPushButton(lang_mgr.get_text("automation.start_scheduler"))
        self._btn_start_scheduler.setMinimumWidth(140)
        self._btn_start_scheduler.setStyleSheet(
            "QPushButton { background:#1e66f5; color:#fff; border:none; border-radius:7px;"
            " padding:7px 16px; font-weight:600; }"
            "QPushButton:hover { background:#1554d4; }"
        )
        icons.set_primary_button_icon(self._btn_start_scheduler, 'deploy', size=QSize(14, 14))
        self._btn_start_scheduler.clicked.connect(self._toggle_scheduler)
        sched_btns.addWidget(self._btn_start_scheduler)

        right_lay.addLayout(sched_btns)

        # Таблица расписаний
        self._sched_table = QTableWidget(0, 5)
        self._sched_table.setHorizontalHeaderLabels([
            lang_mgr.get_text("automation.col_enabled"),
            lang_mgr.get_text("automation.col_name"),
            lang_mgr.get_text("automation.col_interval"),
            lang_mgr.get_text("automation.col_last_run"),
            lang_mgr.get_text("automation.col_next_run"),
        ])
        self._sched_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._sched_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._sched_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._sched_table.setAlternatingRowColors(True)
        self._sched_table.verticalHeader().setVisible(False)
        self._sched_table.setColumnWidth(0, 60)
        right_lay.addWidget(self._sched_table, 1)

        # Лог планировщика
        sched_log_group = QGroupBox(lang_mgr.get_text("automation.scheduler_log"))
        sched_log_lay = QVBoxLayout(sched_log_group)
        self._sched_log = QTextEdit()
        self._sched_log.setReadOnly(True)
        self._sched_log.setFont(QFont("Consolas", 9))
        self._sched_log.setMaximumHeight(120)
        self._sched_log.setStyleSheet(
            "QTextEdit { background:#f8f9fc; border:1px solid #dce0e8;"
            " border-radius:7px; padding:6px; }"
        )
        sched_log_lay.addWidget(self._sched_log)
        right_lay.addWidget(sched_log_group)

        splitter.addWidget(right)
        splitter.setSizes([480, 500])

        # Заполняем таблицы
        self._refresh_hooks_table()
        self._refresh_sched_table()

        return tab

    # ── Хуки ─────────────────────────────────────────────────────────────────

    def _refresh_hooks_table(self):
        t = self._hooks_table
        t.setRowCount(0)
        for hook in self._hooks:
            row = t.rowCount()
            t.insertRow(row)

            chk = QTableWidgetItem('✓' if hook.enabled else '')
            chk.setTextAlignment(Qt.AlignCenter)
            chk.setForeground(QColor('#40a02b' if hook.enabled else '#8c8fa1'))
            t.setItem(row, 0, chk)

            type_item = QTableWidgetItem(hook.type.upper())
            type_item.setForeground(QColor('#1e66f5' if hook.type == 'pre' else '#df8e1d'))
            type_item.setTextAlignment(Qt.AlignCenter)
            t.setItem(row, 1, type_item)

            t.setItem(row, 2, QTableWidgetItem(hook.name))
            t.setItem(row, 3, QTableWidgetItem(hook.command))

            status_text = ''
            status_color = '#8c8fa1'
            if hook.last_exit_code == 0:
                status_text = '✓ OK'
                status_color = '#40a02b'
            elif hook.last_exit_code > 0:
                status_text = f'✗ {hook.last_exit_code}'
                status_color = '#d20f39'
            elif hook.last_exit_code == -1 and hook.last_output:
                status_text = 'Timeout'
                status_color = '#df8e1d'

            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(QColor(status_color))
            status_item.setTextAlignment(Qt.AlignCenter)
            t.setItem(row, 4, status_item)

    def _hook_add(self):
        dlg = HookDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            if not d['name'] or not d['command']:
                return
            hook = Hook(
                id=HooksManager.new_id(), name=d['name'], type=d['type'],
                command=d['command'], enabled=d['enabled'],
                timeout=d['timeout'], stop_on_fail=d['stop_on_fail']
            )
            self._hooks.append(hook)
            HooksManager.save(self._hooks)
            self._refresh_hooks_table()
            self._hooks_log_append(f"Added hook: {hook.name} [{hook.type}]", 'success')

    def _hook_edit(self):
        row = self._hooks_table.currentRow()
        if row < 0 or row >= len(self._hooks):
            return
        hook = self._hooks[row]
        dlg = HookDialog(self, hook)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            hook.name = d['name']; hook.type = d['type']
            hook.command = d['command']; hook.enabled = d['enabled']
            hook.timeout = d['timeout']; hook.stop_on_fail = d['stop_on_fail']
            HooksManager.save(self._hooks)
            self._refresh_hooks_table()
            self._hooks_log_append(f"Updated hook: {hook.name}", 'info')

    def _hook_delete(self):
        row = self._hooks_table.currentRow()
        if row < 0 or row >= len(self._hooks):
            return
        hook = self._hooks.pop(row)
        HooksManager.save(self._hooks)
        self._refresh_hooks_table()
        self._hooks_log_append(f"Deleted hook: {hook.name}", 'warning')

    def _run_hooks_now(self, hook_type: str):
        path = self.path_input.text().strip() if hasattr(self, 'path_input') else ''
        if not path or not os.path.isdir(path):
            self._hooks_log_append(lang_mgr.get_text("automation.no_project_path"), 'error')
            return

        def log(msg, level='info'):
            self._hooks_log_append(msg, level)

        ok = HooksManager.run_hooks(self._hooks, hook_type, path, callback=log)
        self._refresh_hooks_table()
        if ok:
            self._hooks_log_append(f"All {hook_type}-hooks completed OK", 'success')
        else:
            self._hooks_log_append(f"Some {hook_type}-hooks failed", 'error')

    def _hooks_log_append(self, msg: str, level: str = 'info'):
        from datetime import datetime
        colors = {'success': '#40a02b', 'error': '#d20f39',
                  'warning': '#df8e1d', 'info': '#6c6f85'}
        color = colors.get(level, '#6c6f85')
        ts = datetime.now().strftime('%H:%M:%S')
        self._hooks_log.append(
            f'<span style="color:#acb0be;">[{ts}]</span> '
            f'<span style="color:{color};">{msg}</span>'
        )

    # ── Расписание ────────────────────────────────────────────────────────────

    def _refresh_sched_table(self):
        from datetime import datetime
        t = self._sched_table
        t.setRowCount(0)
        interval_labels = {
            'every_30min': lang_mgr.get_text("automation.interval_30min"),
            'every_hour':  lang_mgr.get_text("automation.interval_1h"),
            'every_2h':    lang_mgr.get_text("automation.interval_2h"),
            'every_6h':    lang_mgr.get_text("automation.interval_6h"),
            'every_12h':   lang_mgr.get_text("automation.interval_12h"),
            'every_day':   lang_mgr.get_text("automation.interval_24h"),
        }

        for entry in self._schedules:
            row = t.rowCount()
            t.insertRow(row)

            chk = QTableWidgetItem('✓' if entry.enabled else '')
            chk.setTextAlignment(Qt.AlignCenter)
            chk.setForeground(QColor('#40a02b' if entry.enabled else '#8c8fa1'))
            t.setItem(row, 0, chk)
            t.setItem(row, 1, QTableWidgetItem(entry.name))
            t.setItem(row, 2, QTableWidgetItem(interval_labels.get(entry.interval, entry.interval)))

            def _fmt_dt(iso):
                if not iso:
                    return '—'
                try:
                    return datetime.fromisoformat(iso).strftime('%d.%m %H:%M')
                except Exception:
                    return iso

            last_item = QTableWidgetItem(_fmt_dt(entry.last_run))
            if entry.last_status == 'success':
                last_item.setForeground(QColor('#40a02b'))
            elif entry.last_status == 'error':
                last_item.setForeground(QColor('#d20f39'))
            t.setItem(row, 3, last_item)
            t.setItem(row, 4, QTableWidgetItem(_fmt_dt(entry.next_run)))

    def _sched_add(self):
        repo_names = [r.get('name','') for r in (self.repo_mgr.repos if hasattr(self,'repo_mgr') else [])]
        dlg = ScheduleDialog(self, repo_names=repo_names)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            if not d['name']:
                return
            entry = ScheduleEntry({**d, 'id': ScheduleManager.new_id()})
            self._schedules.append(entry)
            ScheduleManager.save(self._schedules)
            self._refresh_sched_table()
            self._sched_log_append(f"Added schedule: {entry.name}", 'success')

    def _sched_edit(self):
        row = self._sched_table.currentRow()
        if row < 0 or row >= len(self._schedules):
            return
        entry = self._schedules[row]
        repo_names = [r.get('name','') for r in (self.repo_mgr.repos if hasattr(self,'repo_mgr') else [])]
        dlg = ScheduleDialog(self, entry=entry, repo_names=repo_names)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            for k, v in d.items():
                setattr(entry, k, v)
            ScheduleManager.save(self._schedules)
            self._refresh_sched_table()
            self._sched_log_append(f"Updated schedule: {entry.name}", 'info')

    def _sched_delete(self):
        row = self._sched_table.currentRow()
        if row < 0 or row >= len(self._schedules):
            return
        entry = self._schedules.pop(row)
        ScheduleManager.save(self._schedules)
        self._refresh_sched_table()
        self._sched_log_append(f"Deleted schedule: {entry.name}", 'warning')

    def _toggle_scheduler(self):
        if self._scheduler_thread and self._scheduler_thread.isRunning():
            self._scheduler_thread.stop()
            self._scheduler_thread.wait()
            self._scheduler_thread = None
            self._scheduler_status.setText(lang_mgr.get_text("automation.scheduler_stopped"))
            self._scheduler_status.setStyleSheet("font-size:9pt; color:#d20f39; font-weight:600;")
            self._btn_start_scheduler.setText(lang_mgr.get_text("automation.start_scheduler"))
            self._sched_log_append(lang_mgr.get_text("automation.scheduler_stopped"), 'warning')
        else:
            self._scheduler_thread = SchedulerThread()
            self._scheduler_thread.deploy_due.connect(self._on_schedule_due)
            self._scheduler_thread.tick.connect(self._on_scheduler_tick)
            self._scheduler_thread.start()
            self._scheduler_status.setText(lang_mgr.get_text("automation.scheduler_running"))
            self._scheduler_status.setStyleSheet("font-size:9pt; color:#40a02b; font-weight:600;")
            self._btn_start_scheduler.setText(lang_mgr.get_text("automation.stop_scheduler"))
            self._sched_log_append(lang_mgr.get_text("automation.scheduler_started"), 'success')

    def _on_scheduler_tick(self, time_str: str):
        pass   # можно добавить отображение времени

    def _on_schedule_due(self, entry: ScheduleEntry):
        self._sched_log_append(
            f"Auto-deploy: {entry.name} ({entry.repo_name} → {entry.branch})", 'info'
        )
        # Находим репозиторий по имени
        repo = None
        if hasattr(self, 'repo_mgr'):
            for r in self.repo_mgr.repos:
                if r.get('name') == entry.repo_name:
                    repo = r
                    break

        if not repo:
            self._sched_log_append(f"Profile '{entry.repo_name}' not found", 'error')
            entry.mark_run(False)
            ScheduleManager.save(self._schedules)
            return

        path   = repo.get('path', '')
        url    = repo.get('url', '')
        token  = repo.get('token', '') or (self.token_input.text().strip() if hasattr(self,'token_input') else '')
        branch = entry.branch

        # Pre-хуки
        if entry.run_pre:
            ok = HooksManager.run_hooks(
                self._hooks, 'pre', path,
                callback=lambda m, l='info': self._sched_log_append(m, l)
            )
            if not ok:
                self._sched_log_append(f"Pre-hook failed — skipping deploy: {entry.name}", 'error')
                entry.mark_run(False)
                ScheduleManager.save(self._schedules)
                self._refresh_sched_table()
                return

        # Деплой
        from ui.deploy_thread import DeployThread
        thread = DeployThread(path, url, token, entry.commit_msg, True, branch, False)

        def on_log(msg, level='info'):
            self._sched_log_append(f"  {msg}", level)

        def on_finished(success, branch_or_err):
            entry.mark_run(success)
            # Post-хуки (всегда, даже если деплой упал)
            if entry.run_post:
                HooksManager.run_hooks(
                    self._hooks, 'post', path,
                    callback=lambda m, l='info': self._sched_log_append(m, l)
                )
            ScheduleManager.save(self._schedules)
            self._refresh_sched_table()
            status = 'success' if success else 'error'
            self._sched_log_append(
                f"Schedule '{entry.name}' finished: {'OK' if success else branch_or_err}", status
            )

        thread.log_signal.connect(on_log)
        thread.finished_signal.connect(on_finished)
        thread.start()
        self._sched_log_append(f"Started deploy: {entry.name}", 'info')

    def _sched_log_append(self, msg: str, level: str = 'info'):
        from datetime import datetime
        colors = {'success': '#40a02b', 'error': '#d20f39',
                  'warning': '#df8e1d', 'info': '#6c6f85'}
        color = colors.get(level, '#6c6f85')
        ts = datetime.now().strftime('%H:%M:%S')
        self._sched_log.append(
            f'<span style="color:#acb0be;">[{ts}]</span> '
            f'<span style="color:{color};">{msg}</span>'
        )
