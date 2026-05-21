# ui/batch_tab.py
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QCheckBox, QTextEdit, QProgressBar, QFrame,
    QScrollArea, QSizePolicy, QComboBox, QLineEdit, QSplitter, QFrame
)
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from utils.lang_manager import lang_mgr
from utils.icon_manager import IconManager


# ── Поток для группового деплоя ─────────────────────────────────────────────

class BatchDeployThread(QThread):
    project_started  = pyqtSignal(int, str)          # index, name
    project_log      = pyqtSignal(int, str, str)     # index, msg, level
    project_finished = pyqtSignal(int, bool, str)    # index, success, msg
    all_finished     = pyqtSignal(int, int)          # success_count, total

    def __init__(self, tasks, commit_msg, token, do_gitignore, branch):
        super().__init__()
        self.tasks       = tasks        # list of repo dicts
        self.commit_msg  = commit_msg
        self.token       = token
        self.do_gitignore = do_gitignore
        self.branch      = branch
        self._stop       = False

    def stop(self):
        self._stop = True

    def run(self):
        from ui.deploy_thread import DeployThread
        from utils.git_helper import GitHelper
        from config import DEFAULT_GITIGNORE
        from datetime import datetime
        from utils.history import CommitHistoryManager

        success_count = 0

        for i, repo in enumerate(self.tasks):
            if self._stop:
                break

            name   = repo.get('name', f'Project {i+1}')
            path   = repo.get('path', '')
            url    = repo.get('url', '')
            branch = repo.get('branch', self.branch) or self.branch
            token  = repo.get('token', '') or self.token

            self.project_started.emit(i, name)

            def log(msg, level='info', _i=i):
                self.project_log.emit(_i, msg, level)

            try:
                if not os.path.isdir(path):
                    raise Exception(f"Folder not found: {path}")
                if not url:
                    raise Exception("Repository URL is empty")

                # Init
                if not GitHelper.is_git_repo(path):
                    log("Initializing git repo...")
                    GitHelper.run_cmd(['init'], path, log)
                    GitHelper.run_cmd(['branch', '-M', 'main'], path, log)

                # .gitignore
                if self.do_gitignore:
                    gi = os.path.join(path, '.gitignore')
                    if not os.path.exists(gi):
                        with open(gi, 'w', encoding='utf-8') as f:
                            f.write(DEFAULT_GITIGNORE)
                        log("Created .gitignore", 'success')

                # Remote
                GitHelper.run_cmd(['remote', 'remove', 'origin'], path)
                GitHelper.run_cmd(['remote', 'add', 'origin', url], path, log)

                # Branch
                cur = GitHelper.get_current_branch(path)
                if cur != branch:
                    ok, _ = GitHelper.run_cmd(['checkout', branch], path, log)
                    if not ok:
                        GitHelper.run_cmd(['checkout', '-b', branch], path, log)

                # Stage
                GitHelper.run_cmd(['add', '-A'], path, log)

                # Commit
                msg = self.commit_msg or f"Update {datetime.now().strftime('%H:%M')}"
                if GitHelper.has_changes(path):
                    GitHelper.run_cmd(['config', 'user.email', 'helper@local'], path)
                    GitHelper.run_cmd(['config', 'user.name',  'Deploy Helper'],  path)
                    ok, err = GitHelper.run_cmd(['commit', '-m', msg], path, log)
                    if not ok:
                        raise Exception(err or "Commit failed")
                else:
                    log("No changes to commit", 'warning')

                # Push
                log(f"Pushing to {branch}...")
                success, err = GitHelper.push(
                    path, branch=branch,
                    token=token, repo_url=url,
                    callback=log, force=True
                )

                if success:
                    log(f" Done: {name}", 'success')
                    success_count += 1
                    self.project_finished.emit(i, True, "")
                else:
                    raise Exception(err or "Push failed")

            except Exception as e:
                log(f" Error: {e}", 'error')
                self.project_finished.emit(i, False, str(e))

        self.all_finished.emit(success_count, len(self.tasks))


# ── Карточка одного проекта ──────────────────────────────────────────────────

class ProjectCard(QFrame):
    removed = pyqtSignal(object)   # self

    def __init__(self, repo_data, parent=None):
        super().__init__(parent)
        self.repo_data = repo_data
        self._build_ui()
        self.set_status('idle')

    def _build_ui(self):
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            ProjectCard {
                background: #ffffff;
                border: 1.5px solid #dce0e8;
                border-radius: 10px;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(6)

        # ── Заголовок ────────────────────────────────────────────────
        header = QHBoxLayout()

        self.check = QCheckBox()
        self.check.setChecked(True)
        header.addWidget(self.check)

        self.name_label = QLabel(self.repo_data.get('name', 'Project'))
        self.name_label.setStyleSheet("font-weight: 600; font-size: 10.5pt; color: #4c4f69;")
        header.addWidget(self.name_label, 1)

        self.status_label = QLabel()
        self.status_label.setFixedWidth(80)
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.status_label.setStyleSheet("font-size: 9pt; font-weight: 600;")
        header.addWidget(self.status_label)

        remove_btn = QPushButton("")
        remove_btn.setFixedSize(22, 22)
        remove_btn.setStyleSheet("""
            QPushButton {
                background: transparent; border: none;
                color: #9ca0ae; font-size: 12px;
                border-radius: 4px;
            }
            QPushButton:hover { background: #fee2e2; color: #d20f39; }
        """)
        remove_btn.clicked.connect(lambda: self.removed.emit(self))
        header.addWidget(remove_btn)

        root.addLayout(header)

        # ── Инфо строка ──────────────────────────────────────────────
        info = QHBoxLayout()
        info.setSpacing(16)

        path = self.repo_data.get('path', '')
        url  = self.repo_data.get('url', '')
        br   = self.repo_data.get('branch', 'main')

        for icon, text in [("", path), ("", url), ("", br)]:
            lbl = QLabel(f"{icon} {text}" if text else f"{icon} —")
            lbl.setStyleSheet("font-size: 8.5pt; color: #6c6f85;")
            lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            info.addWidget(lbl)

        info.addStretch()
        root.addLayout(info)

        # ── Прогресс-бар ─────────────────────────────────────────────
        self.progress = QProgressBar()
        self.progress.setMaximumHeight(5)
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar { background: #e6e9ef; border: none; border-radius: 3px; }
            QProgressBar::chunk { background: #1e66f5; border-radius: 3px; }
        """)
        root.addWidget(self.progress)

        # ── Мини-лог ─────────────────────────────────────────────────
        self.log_label = QLabel("")
        self.log_label.setStyleSheet("font-size: 8.5pt; color: #8c8fa1;")
        self.log_label.setWordWrap(True)
        root.addWidget(self.log_label)

    def set_status(self, status, text=""):
        styles = {
            'idle':     ("Waiting",   "#8c8fa1"),
            'running':  ("Running...", "#1e66f5"),
            'success':  (" Done",    "#40a02b"),
            'error':    (" Failed",  "#d20f39"),
            'skipped':  ("Skipped",   "#df8e1d"),
        }
        label, color = styles.get(status, ("", "#8c8fa1"))
        self.status_label.setText(label)
        self.status_label.setStyleSheet(f"font-size: 9pt; font-weight: 600; color: {color};")

        if status == 'running':
            self.progress.setVisible(True)
            self.setStyleSheet("""
                ProjectCard {
                    background: #f0f4ff;
                    border: 1.5px solid #89b4fa;
                    border-radius: 10px;
                }
            """)
        elif status == 'success':
            self.progress.setVisible(False)
            self.setStyleSheet("""
                ProjectCard {
                    background: #f0fdf4;
                    border: 1.5px solid #86efac;
                    border-radius: 10px;
                }
            """)
        elif status == 'error':
            self.progress.setVisible(False)
            self.setStyleSheet("""
                ProjectCard {
                    background: #fff1f2;
                    border: 1.5px solid #fca5a5;
                    border-radius: 10px;
                }
            """)
        else:
            self.progress.setVisible(False)
            self.setStyleSheet("""
                ProjectCard {
                    background: #ffffff;
                    border: 1.5px solid #dce0e8;
                    border-radius: 10px;
                }
            """)

    def add_log(self, msg, level='info'):
        colors = {'success': '#40a02b', 'error': '#d20f39',
                  'warning': '#df8e1d', 'info': '#6c6f85'}
        color = colors.get(level, '#6c6f85')
        self.log_label.setStyleSheet(f"font-size: 8.5pt; color: {color};")
        self.log_label.setText(msg[-120:])   # последние 120 символов

    def is_selected(self):
        return self.check.isChecked()


# ── Вкладка Batch Deploy ─────────────────────────────────────────────────────

class BatchTabMixin:

    def _create_batch_tab(self):
        self._batch_cards = []
        self._batch_thread = None
        icons = IconManager()

        tab = QWidget()
        root = QVBoxLayout(tab)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter)

        # ══ ЛЕВАЯ ПАНЕЛЬ — список проектов ══════════════════════════════
        left = QWidget()
        left.setMinimumWidth(360)
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(12, 12, 6, 12)
        left_lay.setSpacing(8)

        # Заголовок
        hdr = QHBoxLayout()
        title = QLabel(lang_mgr.get_text("batch_deploy.title"))
        title.setStyleSheet("font-size: 12pt; font-weight: 700; color: #4c4f69;")
        hdr.addWidget(title)
        hdr.addStretch()

        count_lbl = QLabel("0 projects")
        count_lbl.setStyleSheet("font-size: 9pt; color: #8c8fa1;")
        self._batch_count_label = count_lbl
        hdr.addWidget(count_lbl)
        left_lay.addLayout(hdr)

        # Кнопки управления проектами
        ctrl = QHBoxLayout()
        ctrl.setSpacing(6)

        btn_add_profile = QPushButton(lang_mgr.get_text("batch_deploy.add_from_profiles"))
        btn_add_profile.setStyleSheet(
            "QPushButton { background:#e8f0fe; color:#1e66f5; border:1px solid #b8d0fb; border-radius:7px; padding:6px 12px; font-weight:500; }"
            "QPushButton:hover { background:#d0e4fd; }"
        )
        icons.set_button_icon(btn_add_profile, 'add', color='#1e66f5', size=QSize(14, 14))
        btn_add_profile.clicked.connect(self._batch_add_from_profiles)
        ctrl.addWidget(btn_add_profile)

        btn_add_folder = QPushButton(lang_mgr.get_text("batch_deploy.add_folder"))
        icons.set_button_icon(btn_add_folder, 'folder', size=QSize(14, 14))
        btn_add_folder.clicked.connect(self._batch_add_folder)
        ctrl.addWidget(btn_add_folder)

        btn_clear = QPushButton(lang_mgr.get_text("batch_deploy.clear_all"))
        btn_clear.setStyleSheet(
            "QPushButton { color:#d20f39; border-color:#fca5a5; }"
            "QPushButton:hover { background:#fff1f2; }"
        )
        icons.set_danger_button_icon(btn_clear, 'clear', size=QSize(14, 14))
        btn_clear.clicked.connect(self._batch_clear_all)
        ctrl.addWidget(btn_clear)
        left_lay.addLayout(ctrl)

        # Область карточек
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: #f5f7fb; border-radius: 8px; }")

        self._batch_cards_widget = QWidget()
        self._batch_cards_widget.setStyleSheet("background: transparent;")
        self._batch_cards_layout = QVBoxLayout(self._batch_cards_widget)
        self._batch_cards_layout.setContentsMargins(4, 4, 4, 4)
        self._batch_cards_layout.setSpacing(6)
        self._batch_cards_layout.addStretch()

        scroll.setWidget(self._batch_cards_widget)
        left_lay.addWidget(scroll, 1)

        # Select all / Deselect all — вне скролла, всегда видны
        sel_panel = QWidget()
        sel_row = QHBoxLayout(sel_panel)
        sel_row.setContentsMargins(0, 4, 0, 0)
        btn_sel_all = QPushButton(lang_mgr.get_text("batch_deploy.select_all"))
        btn_sel_all.clicked.connect(lambda: self._batch_toggle_all(True))
        sel_row.addWidget(btn_sel_all)
        btn_desel_all = QPushButton(lang_mgr.get_text("batch_deploy.deselect_all"))
        btn_desel_all.clicked.connect(lambda: self._batch_toggle_all(False))
        sel_row.addWidget(btn_desel_all)
        sel_row.addStretch()
        left_lay.addWidget(sel_panel)

        splitter.addWidget(left)

        # ══ ПРАВАЯ ПАНЕЛЬ — настройки и лог ════════════════════════════
        right = QWidget()
        right.setMinimumWidth(380)
        right_outer = QVBoxLayout(right)
        right_outer.setContentsMargins(0, 0, 0, 0)
        right_outer.setSpacing(0)

        # Прокручиваемая область для настроек
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setFrameShape(QFrame.NoFrame)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        right_content = QWidget()
        right_lay = QVBoxLayout(right_content)
        right_lay.setContentsMargins(6, 12, 12, 8)
        right_lay.setSpacing(10)
        right_scroll.setWidget(right_content)
        right_outer.addWidget(right_scroll, 1)

        # Общие параметры деплоя
        params_group = QGroupBox(lang_mgr.get_text("batch_deploy.deploy_params"))
        params_lay = QVBoxLayout(params_group)
        params_lay.setSpacing(8)

        # Commit message
        params_lay.addWidget(QLabel(lang_mgr.get_text("batch_deploy.commit_label")))
        self._batch_commit = QComboBox()
        self._batch_commit.setEditable(True)
        self._batch_commit.addItems(self.commit_history)
        self._batch_commit.setPlaceholderText(lang_mgr.get_text("batch_deploy.commit_placeholder"))
        params_lay.addWidget(self._batch_commit)

        # Branch
        br_row = QHBoxLayout()
        br_row.addWidget(QLabel(lang_mgr.get_text("batch_deploy.branch_label")))
        self._batch_branch = QComboBox()
        self._batch_branch.setEditable(True)
        self._batch_branch.addItems(["main", "develop", "master"])
        self._batch_branch.setToolTip(lang_mgr.get_text("batch_deploy.branch_tooltip"))
        br_row.addWidget(self._batch_branch)
        params_lay.addLayout(br_row)

        # Token
        params_lay.addWidget(QLabel(lang_mgr.get_text("batch_deploy.token_label")))
        token_row = QHBoxLayout()
        self._batch_token = QLineEdit()
        self._batch_token.setEchoMode(QLineEdit.Password)
        self._batch_token.setPlaceholderText(lang_mgr.get_text("batch_deploy.token_placeholder"))
        token_row.addWidget(self._batch_token)
        btn_use_main = QPushButton(lang_mgr.get_text("batch_deploy.use_main_token"))
        btn_use_main.setMinimumWidth(150)
        btn_use_main.clicked.connect(self._batch_copy_main_token)
        token_row.addWidget(btn_use_main)
        params_lay.addLayout(token_row)

        # Options
        self._batch_gitignore_check = QCheckBox(lang_mgr.get_text("batch_deploy.gitignore_check"))
        self._batch_gitignore_check.setChecked(True)
        params_lay.addWidget(self._batch_gitignore_check)

        right_lay.addWidget(params_group)

        # Статистика
        stats_group = QGroupBox(lang_mgr.get_text("batch_deploy.stats_group"))
        stats_lay = QHBoxLayout(stats_group)
        stats_lay.setSpacing(0)

        for attr, label_key, color in [
            ('_stat_total',   'batch_deploy.stat_total',   '#4c4f69'),
            ('_stat_success', 'batch_deploy.stat_success', '#40a02b'),
            ('_stat_failed',  'batch_deploy.stat_failed',  '#d20f39'),
            ('_stat_pending', 'batch_deploy.stat_pending', '#8c8fa1'),
        ]:
            box = QWidget()
            box_lay = QVBoxLayout(box)
            box_lay.setAlignment(Qt.AlignCenter)
            box_lay.setContentsMargins(0, 4, 0, 4)

            num = QLabel("0")
            num.setAlignment(Qt.AlignCenter)
            num.setStyleSheet(f"font-size: 22pt; font-weight: 700; color: {color};")
            setattr(self, attr + '_lbl', num)
            box_lay.addWidget(num)

            lbl = QLabel(lang_mgr.get_text(label_key))
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size: 8.5pt; color: #8c8fa1;")
            box_lay.addWidget(lbl)

            stats_lay.addWidget(box, 1)

        right_lay.addWidget(stats_group)

        # Общий прогресс
        prog_group = QGroupBox(lang_mgr.get_text("batch_deploy.progress_group"))
        prog_lay = QVBoxLayout(prog_group)
        self._batch_progress = QProgressBar()
        self._batch_progress.setMaximumHeight(12)
        self._batch_progress.setValue(0)
        self._batch_progress.setStyleSheet("""
            QProgressBar { background:#e6e9ef; border:none; border-radius:5px; }
            QProgressBar::chunk {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #1e66f5,stop:1 #40a02b);
                border-radius:5px;
            }
        """)
        prog_lay.addWidget(self._batch_progress)
        self._batch_progress_label = QLabel("")
        self._batch_progress_label.setStyleSheet("font-size: 9pt; color: #8c8fa1;")
        prog_lay.addWidget(self._batch_progress_label)
        right_lay.addWidget(prog_group)

        # Общий лог
        log_group = QGroupBox(lang_mgr.get_text("batch_deploy.log_group"))
        log_lay = QVBoxLayout(log_group)
        log_btn_row = QHBoxLayout()
        btn_clear_log = QPushButton(lang_mgr.get_text("batch_deploy.clear_log"))
        btn_clear_log.setMinimumWidth(110)
        icons.set_danger_button_icon(btn_clear_log, 'clear', size=QSize(14, 14))
        btn_clear_log.clicked.connect(lambda: self._batch_log.clear())
        log_btn_row.addWidget(btn_clear_log)
        log_btn_row.addStretch()
        log_lay.addLayout(log_btn_row)

        self._batch_log = QTextEdit()
        self._batch_log.setReadOnly(True)
        self._batch_log.setFont(QFont("Consolas", 9))
        self._batch_log.setMinimumHeight(140)
        self._batch_log.setStyleSheet(
            "QTextEdit { background:#f8f9fc; border:1px solid #dce0e8; border-radius:7px; padding:6px; }"
        )
        log_lay.addWidget(self._batch_log)
        right_lay.addWidget(log_group, 1)

        # Кнопка запуска
        self._batch_deploy_btn = QPushButton(lang_mgr.get_text("batch_deploy.deploy_button"))
        self._batch_deploy_btn.setMinimumHeight(44)
        self._batch_deploy_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e66f5; color: white;
                font-size: 13px; font-weight: 600;
                border: none; border-radius: 9px; padding: 10px 32px;
            }
            QPushButton:hover { background-color: #1554d4; }
            QPushButton:pressed { background-color: #0e44b4; }
            QPushButton:disabled { background-color: #9bb8f5; color: #e0e8ff; }
        """)
        icons.set_primary_button_icon(self._batch_deploy_btn, 'deploy', size=QSize(18, 18))
        self._batch_deploy_btn.clicked.connect(self._batch_start)
        right_lay.addStretch()

        # Кнопки вне скролла — всегда видны
        btn_panel = QWidget()
        btn_panel_lay = QVBoxLayout(btn_panel)
        btn_panel_lay.setContentsMargins(6, 6, 12, 12)
        btn_panel_lay.setSpacing(6)
        btn_panel_lay.addWidget(self._batch_deploy_btn)

        self._batch_stop_btn = QPushButton(lang_mgr.get_text("batch_deploy.stop_button"))
        self._batch_stop_btn.setMinimumHeight(36)
        self._batch_stop_btn.setVisible(False)
        self._batch_stop_btn.setStyleSheet(
            "QPushButton { background:#fff1f2; color:#d20f39; border:1px solid #fca5a5;"
            " border-radius:7px; font-weight:600; }"
            "QPushButton:hover { background:#fee2e2; }"
        )
        icons.set_danger_button_icon(self._batch_stop_btn, 'clear', size=QSize(14, 14))
        self._batch_stop_btn.clicked.connect(self._batch_stop)
        btn_panel_lay.addWidget(self._batch_stop_btn)
        right_outer.addWidget(btn_panel)

        splitter.addWidget(right)
        splitter.setSizes([420, 460])
        return tab

    # ── Добавление проектов ──────────────────────────────────────────────────

    def _batch_add_card(self, repo_data):
        card = ProjectCard(repo_data)
        card.removed.connect(self._batch_remove_card)
        self._batch_cards.append(card)
        # Вставить перед stretch (последний элемент)
        idx = self._batch_cards_layout.count() - 1
        self._batch_cards_layout.insertWidget(idx, card)
        self._batch_update_count()

    def _batch_remove_card(self, card):
        self._batch_cards.remove(card)
        self._batch_cards_layout.removeWidget(card)
        card.deleteLater()
        self._batch_update_count()

    def _batch_add_from_profiles(self):
        repos = self.repo_mgr.repos
        if not repos:
            self._show_warning(lang_mgr.get_text("batch_deploy.no_profiles_title"),
                               lang_mgr.get_text("batch_deploy.no_profiles_msg"))
            return

        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QDialogButtonBox
        dlg = QDialog(self)
        dlg.setWindowTitle(lang_mgr.get_text("batch_deploy.select_profiles_title"))
        dlg.setMinimumWidth(380)
        lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel(lang_mgr.get_text("batch_deploy.select_profiles_hint")))

        lst = QListWidget()
        lst.setSelectionMode(QListWidget.MultiSelection)
        for r in repos:
            item = QListWidgetItem(f"{r.get('name','')}  —  {r.get('path','')}")
            item.setData(Qt.UserRole, r)
            lst.addItem(item)
        lay.addWidget(lst)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        lay.addWidget(btns)

        if dlg.exec_():
            existing_names = {c.repo_data.get('name') for c in self._batch_cards}
            added = 0
            for item in lst.selectedItems():
                r = item.data(Qt.UserRole)
                if r.get('name') not in existing_names:
                    self._batch_add_card(r)
                    added += 1
            self._batch_append_log(f"Added {added} project(s) from profiles", 'success')

    def _batch_add_folder(self):
        from PyQt5.QtWidgets import QFileDialog
        path = QFileDialog.getExistingDirectory(self, lang_mgr.get_text("batch_deploy.choose_folder"))
        if not path:
            return

        name = os.path.basename(path)
        existing = {c.repo_data.get('path') for c in self._batch_cards}
        if path in existing:
            self._show_warning("", lang_mgr.get_text("batch_deploy.already_added"))
            return

        # Попытаться определить remote URL
        from utils.git_helper import GitHelper
        url = ""
        try:
            import subprocess
            res = subprocess.run(['git', 'remote', 'get-url', 'origin'],
                                 cwd=path, capture_output=True, text=True)
            url = res.stdout.strip()
        except:
            pass

        self._batch_add_card({
            'name':   name,
            'path':   path,
            'url':    url,
            'branch': 'main',
            'token':  ''
        })

    def _batch_clear_all(self):
        for card in list(self._batch_cards):
            self._batch_cards_layout.removeWidget(card)
            card.deleteLater()
        self._batch_cards.clear()
        self._batch_update_count()

    def _batch_toggle_all(self, state):
        for card in self._batch_cards:
            card.check.setChecked(state)

    def _batch_copy_main_token(self):
        if hasattr(self, 'token_input'):
            token = self.token_input.text().strip()
            self._batch_token.setText(token)
            self._batch_append_log("Token copied from main tab", 'info')

    def _batch_update_count(self):
        n = len(self._batch_cards)
        self._batch_count_label.setText(
            f"{n} {lang_mgr.get_text('batch_deploy.projects_count')}"
        )
        if hasattr(self, '_stat_total_lbl'):
            self._stat_total_lbl.setText(str(n))

    # ── Запуск ───────────────────────────────────────────────────────────────

    def _batch_start(self):
        selected = [c for c in self._batch_cards if c.is_selected()]
        if not selected:
            self._show_warning(lang_mgr.get_text("batch_deploy.no_selected_title"),
                               lang_mgr.get_text("batch_deploy.no_selected_msg"))
            return

        token  = self._batch_token.text().strip()
        commit = self._batch_commit.currentText().strip()
        branch = self._batch_branch.currentText().strip() or 'main'
        do_gi  = self._batch_gitignore_check.isChecked()

        # Сброс статусов
        for card in self._batch_cards:
            card.set_status('idle')
            card.add_log("")
        self._batch_log.clear()

        n = len(selected)
        self._batch_progress.setMaximum(n)
        self._batch_progress.setValue(0)
        self._stat_success_lbl.setText("0")
        self._stat_failed_lbl.setText("0")
        self._stat_pending_lbl.setText(str(n))
        self._batch_progress_label.setText(
            lang_mgr.get_text("batch_deploy.progress_label").format(done=0, total=n)
        )

        self._batch_deploy_btn.setEnabled(False)
        self._batch_stop_btn.setVisible(True)

        tasks = [c.repo_data for c in selected]
        self._batch_selected_cards = selected
        self._done_count = 0
        self._success_count = 0
        self._fail_count = 0

        self._batch_thread = BatchDeployThread(tasks, commit, token, do_gi, branch)
        self._batch_thread.project_started.connect(self._on_project_started)
        self._batch_thread.project_log.connect(self._on_project_log)
        self._batch_thread.project_finished.connect(self._on_project_finished)
        self._batch_thread.all_finished.connect(self._on_all_finished)
        self._batch_thread.start()

        self._batch_append_log(
            lang_mgr.get_text("batch_deploy.log_started").format(n=n), 'info'
        )

    def _batch_stop(self):
        if self._batch_thread and self._batch_thread.isRunning():
            self._batch_thread.stop()
            self._batch_append_log(lang_mgr.get_text("batch_deploy.log_stopped"), 'warning')

    # ── Слоты потока ────────────────────────────────────────────────────────

    def _on_project_started(self, index, name):
        if index < len(self._batch_selected_cards):
            self._batch_selected_cards[index].set_status('running')
        self._batch_append_log(f"▶  [{index+1}] {name}", 'info')

    def _on_project_log(self, index, msg, level):
        if index < len(self._batch_selected_cards):
            self._batch_selected_cards[index].add_log(msg, level)

    def _on_project_finished(self, index, success, msg):
        self._done_count += 1
        n = len(self._batch_selected_cards)

        if success:
            self._success_count += 1
            if index < len(self._batch_selected_cards):
                self._batch_selected_cards[index].set_status('success')
            self._batch_append_log(
                f" [{index+1}] {self._batch_selected_cards[index].repo_data.get('name','')}", 'success'
            )
        else:
            self._fail_count += 1
            if index < len(self._batch_selected_cards):
                self._batch_selected_cards[index].set_status('error', msg)
            self._batch_append_log(
                f" [{index+1}] {self._batch_selected_cards[index].repo_data.get('name','')} — {msg}", 'error'
            )

        self._batch_progress.setValue(self._done_count)
        self._stat_success_lbl.setText(str(self._success_count))
        self._stat_failed_lbl.setText(str(self._fail_count))
        self._stat_pending_lbl.setText(str(n - self._done_count))
        self._batch_progress_label.setText(
            lang_mgr.get_text("batch_deploy.progress_label").format(done=self._done_count, total=n)
        )

    def _on_all_finished(self, success, total):
        self._batch_deploy_btn.setEnabled(True)
        self._batch_stop_btn.setVisible(False)

        msg = lang_mgr.get_text("batch_deploy.log_finished").format(
            success=success, total=total, failed=total - success
        )
        self._batch_append_log(msg, 'success' if success == total else 'warning')

        if hasattr(self, 'status_label'):
            self.status_label.setText(
                lang_mgr.get_text("batch_deploy.status_done").format(success=success, total=total)
            )

    def _batch_append_log(self, msg, level='info'):
        from datetime import datetime
        colors = {'success': '#40a02b', 'error': '#d20f39',
                  'warning': '#df8e1d', 'info': '#6c6f85'}
        color = colors.get(level, '#6c6f85')
        ts = datetime.now().strftime('%H:%M:%S')
        self._batch_log.append(
            f'<span style="color:#acb0be;">[{ts}]</span> '
            f'<span style="color:{color};">{msg}</span>'
        )
