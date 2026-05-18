# ui/about_tab.py
import webbrowser
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QGroupBox,
    QFrame, QScrollArea
)
from PyQt5.QtCore import Qt

from utils.lang_manager import lang_mgr


class AboutTabMixin:

    def _create_about_tab(self):
        tab = QWidget()
        root = QVBoxLayout(tab)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        root.addWidget(scroll)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        scroll.setWidget(content)

        # ── Header card ──────────────────────────────────────────────────
        header = QFrame()
        header.setStyleSheet(
            "QFrame { background-color: #1e66f5; border-radius: 12px; padding: 24px; }"
        )
        header_layout = QVBoxLayout(header)

        title = QLabel(lang_mgr.get_text("app_name"))
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #ffffff;")
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)

        version = QLabel(lang_mgr.get_text("version"))
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.8);")
        header_layout.addWidget(version)

        layout.addWidget(header)

        # ── Description ──────────────────────────────────────────────────
        desc_group = QGroupBox(lang_mgr.get_text("about_tab.description_group"))
        desc_layout = QVBoxLayout(desc_group)

        # Преобразуем \n и • в HTML для корректного рендеринга
        raw = lang_mgr.get_text("about_tab.description")
        html = self._text_to_html(raw)

        description = QLabel()
        description.setTextFormat(Qt.RichText)
        description.setText(html)
        description.setWordWrap(True)
        description.setStyleSheet("font-size: 10pt; color: #4c4f69; line-height: 1.6;")
        desc_layout.addWidget(description)
        layout.addWidget(desc_group)

        # ── Links ────────────────────────────────────────────────────────
        links_group = QGroupBox(lang_mgr.get_text("about_tab.links_group"))
        links_layout = QVBoxLayout(links_group)
        links_layout.setSpacing(8)

        for text_key, url in [
            ("about_tab.token_link",    "https://github.com/settings/tokens"),
            ("about_tab.git_link",      "https://git-scm.com/doc"),
            ("about_tab.branches_link", "https://git-scm.com/book/en/v2/Git-Branching-Branches-in-a-Nutshell"),
        ]:
            btn = QPushButton(lang_mgr.get_text(text_key))
            btn.setStyleSheet(
                "QPushButton { text-align: left; background: transparent;"
                " border: 1px solid #dce0e8; color: #1e66f5;"
                " padding: 10px 14px; border-radius: 7px; font-size: 10pt; }"
                "QPushButton:hover { background-color: #e8f0fe; border-color: #89b4fa; }"
            )
            btn.clicked.connect(lambda checked, u=url: webbrowser.open(u))
            links_layout.addWidget(btn)

        layout.addWidget(links_group)

        credits = QLabel(lang_mgr.get_text("about_tab.credits"))
        credits.setAlignment(Qt.AlignCenter)
        credits.setStyleSheet("color: #8c8fa1; font-size: 9pt;")
        layout.addWidget(credits)

        layout.addStretch()
        return tab

    @staticmethod
    def _text_to_html(text: str) -> str:
        """Конвертирует plain-text с \n и • в HTML."""
        lines = text.split('\n')
        html_parts = []
        for line in lines:
            line = line.strip()
            if not line:
                html_parts.append('<br>')
            elif line.startswith('•'):
                item = line[1:].strip()
                html_parts.append(
                    f'<span style="color:#1e66f5; font-weight:600;">•</span>'
                    f'&nbsp;{item}<br>'
                )
            else:
                # Заголовки разделов (строки без отступа, заканчивающиеся :)
                if line.endswith(':'):
                    html_parts.append(
                        f'<b style="color:#4c4f69;">{line}</b><br>'
                    )
                else:
                    html_parts.append(f'{line}<br>')
        return ''.join(html_parts)

    def _show_help(self):
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            lang_mgr.get_text("dialogs.help.title"),
            lang_mgr.get_text("dialogs.help.content")
        )

    def _show_about(self):
        """Переключает на вкладку About по ключу (не хардкодит индекс)."""
        idx = self._tab_index_by_key('about')
        self.tabs.setCurrentIndex(idx)
