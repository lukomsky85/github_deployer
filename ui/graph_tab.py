# ui/graph_tab.py
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QScrollArea, QFrame, QSplitter, QTextEdit,
    QComboBox, QLineEdit, QSizePolicy, QSpinBox, QCheckBox
)
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from utils.lang_manager import lang_mgr
from utils.icon_manager import IconManager
from utils.git_graph import GitGraph, CommitNode
from ui.graph_widget import CommitGraphWidget


# ── Поток загрузки ───────────────────────────────────────────────────────────

class GraphLoadThread(QThread):
    loaded = pyqtSignal(list)
    error  = pyqtSignal(str)

    def __init__(self, path, max_commits):
        super().__init__()
        self.path = path
        self.max_commits = max_commits

    def run(self):
        try:
            commits = GitGraph.load(self.path, self.max_commits)
            self.loaded.emit(commits)
        except Exception as e:
            self.error.emit(str(e))


# ── Панель деталей коммита ───────────────────────────────────────────────────

class CommitDetailPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        # Заголовок
        self._title = QLabel(lang_mgr.get_text("graph_tab.detail_placeholder"))
        self._title.setWordWrap(True)
        self._title.setStyleSheet(
            "font-size: 11pt; font-weight: 600; color: #4c4f69; padding: 4px 0;"
        )
        lay.addWidget(self._title)

        # SHA + кнопка копировать
        sha_row = QHBoxLayout()
        self._sha_label = QLabel("")
        self._sha_label.setStyleSheet(
            "font-family: Consolas, monospace; font-size: 9pt; color: #89b4fa;"
            " background: #f0f4ff; border-radius: 5px; padding: 3px 8px;"
        )
        self._sha_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        sha_row.addWidget(self._sha_label)

        self._copy_btn = QPushButton(lang_mgr.get_text("graph_tab.copy_sha"))
        self._copy_btn.setMinimumWidth(120)
        self._copy_btn.setStyleSheet(
            "QPushButton { background:#e8f0fe; color:#1e66f5; border:1px solid #b8d0fb;"
            " border-radius:7px; padding:5px 12px; font-size:9pt; }"
            "QPushButton:hover { background:#d0e4fd; }"
        )
        from utils.icon_manager import IconManager as _IM
        _IM().set_button_icon(self._copy_btn, 'save', color='#1e66f5', size=QSize(14, 14))
        self._copy_btn.clicked.connect(self._copy_sha)
        sha_row.addWidget(self._copy_btn)
        sha_row.addStretch()
        lay.addLayout(sha_row)

        # Метаданные
        meta_group = QGroupBox(lang_mgr.get_text("graph_tab.detail_meta"))
        meta_lay = QVBoxLayout(meta_group)
        meta_lay.setSpacing(4)

        for attr in ('_author', '_date', '_branches'):
            lbl = QLabel("")
            lbl.setStyleSheet("font-size: 9pt; color: #6c6f85;")
            lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            setattr(self, attr, lbl)
            meta_lay.addWidget(lbl)

        lay.addWidget(meta_group)

        # Родители
        parents_group = QGroupBox(lang_mgr.get_text("graph_tab.detail_parents"))
        parents_lay = QVBoxLayout(parents_group)
        self._parents_label = QLabel("—")
        self._parents_label.setStyleSheet(
            "font-family: Consolas, monospace; font-size: 9pt; color: #6c6f85;"
        )
        self._parents_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._parents_label.setWordWrap(True)
        parents_lay.addWidget(self._parents_label)
        lay.addWidget(parents_group)

        # Diff / файлы изменённые
        diff_group = QGroupBox(lang_mgr.get_text("graph_tab.detail_files"))
        diff_lay = QVBoxLayout(diff_group)
        self._files_text = QTextEdit()
        self._files_text.setReadOnly(True)
        self._files_text.setFont(QFont("Consolas", 9))
        self._files_text.setMinimumHeight(120)
        self._files_text.setStyleSheet(
            "QTextEdit { background:#f8f9fc; border:1px solid #dce0e8;"
            " border-radius:7px; padding:6px; }"
        )
        diff_lay.addWidget(self._files_text)
        lay.addWidget(diff_group, 1)

        lay.addStretch()

        self._current_sha = ""

    def show_commit(self, node: CommitNode, repo_path: str):
        self._current_sha = node.sha
        self._title.setText(node.message)
        self._sha_label.setText(node.sha)
        self._author.setText(f"  {node.author}")
        self._date.setText(f"  {node.date}")
        branches_str = "  ".join(
            f"<span style='background:#1e66f5;color:#fff;"
            f"border-radius:3px;padding:1px 5px;font-size:8pt;'>{b}</span>"
            for b in node.branches
        ) if node.branches else "—"
        self._branches.setText(f"  {branches_str}" if node.branches else "  —")
        self._branches.setTextFormat(Qt.RichText)
        self._parents_label.setText("\n".join(node.parents) if node.parents else "—  (initial commit)")

        # Загружаем список файлов этого коммита
        self._files_text.clear()
        try:
            import subprocess
            res = subprocess.run(
                ["git", "show", "--stat", "--format=", node.sha],
                cwd=repo_path,
                capture_output=True, text=True,
                encoding="utf-8", errors="replace"
            )
            text = res.stdout.strip()
            if not text:
                text = "(no changes)"
            # Раскрасим по типу операции
            html = []
            for line in text.splitlines():
                if line.strip().startswith("+"):
                    color = "#40a02b"
                elif line.strip().startswith("-"):
                    color = "#d20f39"
                elif "|" in line:
                    color = "#4c4f69"
                else:
                    color = "#8c8fa1"
                safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                html.append(f'<span style="color:{color};">{safe}</span>')
            self._files_text.setHtml("<br>".join(html))
        except Exception as e:
            self._files_text.setPlainText(f"Error: {e}")

    def _copy_sha(self):
        if self._current_sha:
            QApplication = __import__('PyQt5.QtWidgets', fromlist=['QApplication']).QApplication
            QApplication.clipboard().setText(self._current_sha)

    def clear(self):
        self._title.setText(lang_mgr.get_text("graph_tab.detail_placeholder"))
        self._sha_label.setText("")
        self._author.setText("")
        self._date.setText("")
        self._branches.setText("")
        self._parents_label.setText("—")
        self._files_text.clear()
        self._current_sha = ""


# ── Вкладка Граф коммитов ────────────────────────────────────────────────────

class GraphTabMixin:

    def _create_graph_tab(self):
        self._graph_repo_path = ""
        icons = IconManager()

        tab = QWidget()
        root = QVBoxLayout(tab)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        # ── Панель управления ────────────────────────────────────────────
        ctrl_group = QGroupBox(lang_mgr.get_text("graph_tab.repo_group"))
        ctrl_lay = QVBoxLayout(ctrl_group)
        ctrl_lay.setSpacing(6)

        # Путь к репо
        path_row = QHBoxLayout()
        path_row.setSpacing(6)

        self._graph_path_input = QLineEdit()
        self._graph_path_input.setPlaceholderText(lang_mgr.get_text("graph_tab.path_placeholder"))
        if hasattr(self, 'default_path'):
            self._graph_path_input.setText(self.default_path)
        path_row.addWidget(self._graph_path_input)

        browse_btn = QPushButton(lang_mgr.get_text("graph_tab.browse"))
        browse_btn.setMinimumWidth(90)
        icons.set_button_icon(browse_btn, 'folder', size=QSize(14, 14))
        browse_btn.clicked.connect(lambda: self._browse_folder(self._graph_path_input))
        path_row.addWidget(browse_btn)

        # Кнопка синхронизации пути из Deploy
        sync_btn = QPushButton(lang_mgr.get_text("graph_tab.sync_path"))
        sync_btn.setMinimumWidth(160)
        sync_btn.setStyleSheet(
            "QPushButton { background:#f0f4ff; color:#1e66f5; border:1px solid #b8d0fb; border-radius:7px; padding:6px 10px; }"
            "QPushButton:hover { background:#dbeafe; }"
        )
        sync_btn.clicked.connect(self._graph_sync_path)
        path_row.addWidget(sync_btn)

        ctrl_lay.addLayout(path_row)

        # Опции
        opts_row = QHBoxLayout()
        opts_row.setSpacing(12)

        opts_row.addWidget(QLabel(lang_mgr.get_text("graph_tab.max_commits")))
        self._graph_max_spin = QSpinBox()
        self._graph_max_spin.setRange(10, 2000)
        self._graph_max_spin.setValue(100)
        self._graph_max_spin.setSingleStep(50)
        self._graph_max_spin.setFixedWidth(90)
        self._graph_max_spin.setFixedHeight(34)
        self._graph_max_spin.setStyleSheet(
            "QSpinBox { background:#fff; border:1.5px solid #ccd0da; border-radius:7px;"
            " padding:4px 8px; color:#4c4f69; }"
            "QSpinBox:focus { border-color:#1e66f5; }"
            "QSpinBox::up-button, QSpinBox::down-button { width:18px; border-radius:4px; }"
        )
        opts_row.addWidget(self._graph_max_spin)

        opts_row.addSpacing(16)

        self._graph_search = QLineEdit()
        self._graph_search.setPlaceholderText(lang_mgr.get_text("graph_tab.search_placeholder"))
        self._graph_search.setFixedWidth(220)
        self._graph_search.textChanged.connect(self._graph_filter)
        opts_row.addWidget(self._graph_search)

        opts_row.addStretch()

        self._graph_refresh_btn = QPushButton(lang_mgr.get_text("graph_tab.refresh"))
        self._graph_refresh_btn.setMinimumWidth(150)
        self._graph_refresh_btn.setStyleSheet(
            "QPushButton { background:#1e66f5; color:#fff; border:none; border-radius:7px;"
            " padding:7px 18px; font-weight:600; }"
            "QPushButton:hover { background:#1554d4; }"
            "QPushButton:disabled { background:#9bb8f5; color:#e0e8ff; }"
        )
        icons.set_primary_button_icon(self._graph_refresh_btn, 'refresh', size=QSize(16, 16))
        self._graph_refresh_btn.clicked.connect(self._graph_load)
        opts_row.addWidget(self._graph_refresh_btn)

        ctrl_lay.addLayout(opts_row)

        # Статус
        self._graph_status_label = QLabel("")
        self._graph_status_label.setStyleSheet("font-size: 9pt; color: #8c8fa1;")
        ctrl_lay.addWidget(self._graph_status_label)

        root.addWidget(ctrl_group)

        # ── Заголовки колонок ────────────────────────────────────────────
        header = QWidget()
        header.setFixedHeight(24)
        header.setStyleSheet("background:#e6e9ef; border-radius:4px;")
        header_lay = QHBoxLayout(header)
        header_lay.setContentsMargins(8, 0, 8, 0)

        for text in [
            lang_mgr.get_text("graph_tab.col_graph"),
            lang_mgr.get_text("graph_tab.col_message"),
            lang_mgr.get_text("graph_tab.col_sha"),
            lang_mgr.get_text("graph_tab.col_author"),
            lang_mgr.get_text("graph_tab.col_date"),
        ]:
            lbl = QLabel(text)
            lbl.setStyleSheet("font-size: 8.5pt; font-weight: 600; color: #6c6f85;")
            header_lay.addWidget(lbl, 1 if text != lang_mgr.get_text("graph_tab.col_graph") else 0)

        root.addWidget(header)

        # ── Splitter: граф слева, детали справа ──────────────────────────
        splitter = QSplitter(Qt.Horizontal)

        # Граф в scroll area
        graph_container = QWidget()
        gc_lay = QVBoxLayout(graph_container)
        gc_lay.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("QScrollArea { background: #ffffff; border: 1px solid #dce0e8; border-radius: 8px; }")

        self._graph_widget = CommitGraphWidget()
        self._graph_widget.commit_selected.connect(self._on_commit_selected)
        scroll.setWidget(self._graph_widget)
        gc_lay.addWidget(scroll)
        splitter.addWidget(graph_container)

        # Панель деталей
        detail_scroll = QScrollArea()
        detail_scroll.setWidgetResizable(True)
        detail_scroll.setFrameShape(QFrame.NoFrame)
        detail_scroll.setMinimumWidth(300)
        detail_scroll.setMaximumWidth(420)
        detail_scroll.setStyleSheet(
            "QScrollArea { background:#ffffff; border:1px solid #dce0e8; border-radius:8px; }"
        )

        self._detail_panel = CommitDetailPanel()
        self._detail_panel.setContentsMargins(12, 12, 12, 12)
        detail_scroll.setWidget(self._detail_panel)
        splitter.addWidget(detail_scroll)

        splitter.setSizes([700, 360])
        root.addWidget(splitter, 1)

        # Все коммиты (для фильтрации)
        self._graph_all_commits = []

        return tab

    # ── Логика ───────────────────────────────────────────────────────────────

    def _graph_sync_path(self):
        """Скопировать путь из вкладки Deploy."""
        if hasattr(self, 'path_input'):
            self._graph_path_input.setText(self.path_input.text())

    def _graph_load(self):
        path = self._graph_path_input.text().strip()
        if not path or not os.path.isdir(path):
            self._graph_status_label.setText(lang_mgr.get_text("graph_tab.error_not_found"))
            self._graph_status_label.setStyleSheet("font-size:9pt; color:#d20f39;")
            return

        from utils.git_helper import GitHelper
        if not GitHelper.is_git_repo(path):
            self._graph_status_label.setText(lang_mgr.get_text("graph_tab.error_not_repo"))
            self._graph_status_label.setStyleSheet("font-size:9pt; color:#d20f39;")
            return

        self._graph_repo_path = path
        self._graph_refresh_btn.setEnabled(False)
        self._graph_status_label.setText(lang_mgr.get_text("graph_tab.loading"))
        self._graph_status_label.setStyleSheet("font-size:9pt; color:#1e66f5;")
        self._graph_widget.set_commits([])
        self._detail_panel.clear()

        max_c = self._graph_max_spin.value()
        self._graph_thread = GraphLoadThread(path, max_c)
        self._graph_thread.loaded.connect(self._on_graph_loaded)
        self._graph_thread.error.connect(self._on_graph_error)
        self._graph_thread.start()

    def _on_graph_loaded(self, commits):
        self._graph_all_commits = commits
        self._graph_refresh_btn.setEnabled(True)
        n = len(commits)

        # Применяем фильтр если есть
        self._graph_filter(self._graph_search.text())

        n_lanes = max((c.col for c in commits), default=0) + 1
        self._graph_status_label.setText(
            lang_mgr.get_text("graph_tab.loaded_status").format(n=n, lanes=n_lanes)
        )
        self._graph_status_label.setStyleSheet("font-size:9pt; color:#40a02b;")

    def _on_graph_error(self, msg):
        self._graph_refresh_btn.setEnabled(True)
        self._graph_status_label.setText(f"Error: {msg}")
        self._graph_status_label.setStyleSheet("font-size:9pt; color:#d20f39;")

    def _graph_filter(self, text):
        text = text.strip().lower()
        if not text:
            filtered = self._graph_all_commits
        else:
            filtered = [
                c for c in self._graph_all_commits
                if text in c.message.lower()
                or text in c.author.lower()
                or text in c.short_sha.lower()
                or any(text in b.lower() for b in c.branches)
            ]
        # Переназначаем row
        for i, c in enumerate(filtered):
            c.row = i
        self._graph_widget.set_commits(filtered)

    def _on_commit_selected(self, node: CommitNode):
        self._detail_panel.show_commit(node, self._graph_repo_path)
