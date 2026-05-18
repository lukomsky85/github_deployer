# ui/graph_widget.py
"""
Виджет отрисовки графа коммитов через QPainter.
"""
from PyQt5.QtWidgets import (
    QWidget, QScrollArea, QAbstractScrollArea, QSizePolicy,
    QToolTip, QApplication
)
from PyQt5.QtCore import Qt, QRect, QPoint, QSize, pyqtSignal
from PyQt5.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QFontMetrics,
    QPainterPath, QCursor
)
from utils.git_graph import GitGraph, CommitNode
from typing import List, Optional


# ── Константы размеров ───────────────────────────────────────────────────────
ROW_H      = 34   # высота строки
DOT_R      = 7    # радиус точки коммита
LANE_W     = 22   # ширина дорожки
GRAPH_PAD  = 10   # отступ слева
TEXT_PAD   = 8    # отступ текста от графа


class CommitGraphWidget(QWidget):
    """
    Кастомный виджет — рисует граф коммитов через QPainter.
    Поддерживает: клик (выделение), hover (подсветка), тултип.
    """
    commit_selected = pyqtSignal(object)  # CommitNode

    def __init__(self, parent=None):
        super().__init__(parent)
        self.commits: List[CommitNode] = []
        self.selected_sha: Optional[str] = None
        self.hovered_row:  Optional[int] = None
        self._graph_width  = 0   # ширина графика (px)
        self._n_lanes      = 1

        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.ArrowCursor)

    def set_commits(self, commits: List[CommitNode]):
        self.commits = commits
        self._n_lanes = max((c.col for c in commits), default=0) + 1
        self._graph_width = GRAPH_PAD + self._n_lanes * LANE_W + TEXT_PAD
        total_h = max(len(commits) * ROW_H, 40)
        self.setFixedHeight(total_h)
        self.update()

    # ── Paint ────────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        if not self.commits:
            p = QPainter(self)
            p.setPen(QColor("#8c8fa1"))
            p.setFont(QFont("Segoe UI", 10))
            p.drawText(self.rect(), Qt.AlignCenter, "No commits to display.\nSelect a repository and click Refresh.")
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        visible_rect = event.rect()

        # Определяем диапазон строк для отрисовки (оптимизация)
        row_start = max(0, visible_rect.top() // ROW_H)
        row_end   = min(len(self.commits), visible_rect.bottom() // ROW_H + 2)

        # ── 1. Рисуем линии (edges) ──────────────────────────────────────
        sha_map = {c.sha: i for i, c in enumerate(self.commits)}

        for row in range(row_start, row_end):
            node = self.commits[row]
            cx, cy = self._pos(node)

            for psha in node.parents:
                pidx = sha_map.get(psha)
                if pidx is None:
                    continue
                pnode = self.commits[pidx]
                pcx, pcy = self._pos(pnode)

                color = QColor(GitGraph.get_color(node.col))
                pen = QPen(color, 2, Qt.SolidLine)
                pen.setCapStyle(Qt.RoundCap)
                p.setPen(pen)

                if node.col == pnode.col:
                    # Прямая вертикальная линия
                    p.drawLine(cx, cy, pcx, pcy)
                else:
                    # Изогнутая линия (bezier)
                    path = QPainterPath()
                    path.moveTo(cx, cy)
                    mid_y = (cy + pcy) / 2
                    path.cubicTo(cx, mid_y, pcx, mid_y, pcx, pcy)
                    p.drawPath(path)

        # ── 2. Рисуем строки ─────────────────────────────────────────────
        font_msg    = QFont("Segoe UI", 9)
        font_meta   = QFont("Segoe UI", 8)
        font_badge  = QFont("Segoe UI", 7, QFont.Bold)
        fm_msg  = QFontMetrics(font_msg)
        fm_meta = QFontMetrics(font_meta)

        for row in range(row_start, row_end):
            node = self.commits[row]
            cx, cy = self._pos(node)
            row_y = row * ROW_H

            # Фон строки (hover / selected)
            if node.sha == self.selected_sha:
                p.fillRect(0, row_y, w, ROW_H, QColor("#dbeafe"))
            elif row == self.hovered_row:
                p.fillRect(0, row_y, w, ROW_H, QColor("#f0f4ff"))

            # Точка коммита
            dot_color = QColor(GitGraph.get_color(node.col))
            p.setPen(QPen(dot_color.darker(120), 1.5))
            p.setBrush(QBrush(dot_color if node.sha != self.selected_sha else QColor("#1e66f5")))
            p.drawEllipse(QPoint(cx, cy), DOT_R, DOT_R)

            # Текст начинается после графической зоны
            tx = self._graph_width

            # Бейджи веток
            bx = tx
            for branch in node.branches:
                is_head = branch.startswith("HEAD") or "HEAD" in branch
                is_tag  = branch.startswith("🏷")
                bg = QColor("#1e66f5") if is_head else (QColor("#df8e1d") if is_tag else QColor("#40a02b"))
                text = branch[:18] + ("…" if len(branch) > 18 else "")
                bw = fm_badge.horizontalAdvance(text) + 10
                bh = 16
                by = row_y + (ROW_H - bh) // 2
                p.setFont(font_badge)
                p.setBrush(QBrush(bg))
                p.setPen(Qt.NoPen)
                p.drawRoundedRect(bx, by, bw, bh, 4, 4)
                p.setPen(QColor("#ffffff"))
                p.drawText(bx + 5, by + bh - 4, text)
                bx += bw + 4

            # Сообщение коммита
            msg_x = bx + (4 if node.branches else 0)
            avail_w = w - msg_x - 300  # оставляем место для автора+даты
            p.setFont(font_msg)
            p.setPen(QColor("#4c4f69") if node.sha != self.selected_sha else QColor("#1554d4"))
            msg_clipped = fm_msg.elidedText(node.message, Qt.ElideRight, max(avail_w, 100))
            p.drawText(msg_x, row_y + ROW_H // 2 + fm_msg.ascent() // 2 - 1, msg_clipped)

            # SHA
            sha_x = w - 280
            p.setFont(font_meta)
            p.setPen(QColor("#89b4fa"))
            p.drawText(sha_x, row_y + ROW_H // 2 + fm_meta.ascent() // 2 - 1, node.short_sha)

            # Автор
            auth_x = w - 230
            p.setPen(QColor("#6c6f85"))
            author_clipped = fm_meta.elidedText(node.author, Qt.ElideRight, 120)
            p.drawText(auth_x, row_y + ROW_H // 2 + fm_meta.ascent() // 2 - 1, author_clipped)

            # Дата
            date_x = w - 105
            p.setPen(QColor("#8c8fa1"))
            p.drawText(date_x, row_y + ROW_H // 2 + fm_meta.ascent() // 2 - 1, node.date)

        p.end()

    # ── Mouse ────────────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        row = event.y() // ROW_H
        if 0 <= row < len(self.commits):
            node = self.commits[row]
            self.selected_sha = node.sha
            self.update()
            self.commit_selected.emit(node)

    def mouseMoveEvent(self, event):
        row = event.y() // ROW_H
        new_hover = row if 0 <= row < len(self.commits) else None
        if new_hover != self.hovered_row:
            self.hovered_row = new_hover
            self.update()

        if new_hover is not None:
            node = self.commits[new_hover]
            tip = f"<b>{node.message}</b><br>{node.author} · {node.date}<br><code>{node.sha[:16]}</code>"
            QToolTip.showText(event.globalPos(), tip, self)

    def leaveEvent(self, event):
        self.hovered_row = None
        self.update()

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _pos(self, node: CommitNode):
        """Центр точки коммита (x, y) для данного узла."""
        x = GRAPH_PAD + node.col * LANE_W + LANE_W // 2
        y = node.row * ROW_H + ROW_H // 2
        return x, y
