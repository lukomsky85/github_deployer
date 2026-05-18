# ui/toolbar.py
from PyQt5.QtWidgets import QToolBar, QAction, QWidget, QLabel, QSizePolicy
from PyQt5.QtCore import QSize, Qt

from utils.lang_manager import lang_mgr
from utils.icon_manager import IconManager


class ToolbarMixin:

    def _setup_toolbar(self):
        self._icons = IconManager()
        self._toolbar = QToolBar()
        self._toolbar.setMovable(False)
        self._toolbar.setIconSize(QSize(20, 20))
        # Только иконки — без текста
        self._toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.addToolBar(self._toolbar)
        self._fill_toolbar()

    def _fill_toolbar(self):
        """Заполняет тулбар экшенами. Вызывается при старте и при смене языка."""
        self._toolbar.clear()

        def _action(text_key, icon_name, slot, shortcut=None):
            # Текст идёт в тултип (виден при наведении), не рядом с иконкой
            act = QAction(self)
            act.setToolTip(lang_mgr.get_text(text_key))
            self._icons.set_action_icon(act, icon_name, size=QSize(20, 20))
            act.triggered.connect(slot)
            if shortcut:
                act.setShortcut(shortcut)
                act.setToolTip(f"{lang_mgr.get_text(text_key)}  [{shortcut}]")
            return act

        self._toolbar.addAction(_action("toolbar.deploy",           "deploy",  self.start_deployment, "F5"))
        self._toolbar.addSeparator()
        self._toolbar.addAction(_action("toolbar.refresh_branches", "refresh", self._refresh_branches))
        self._toolbar.addSeparator()
        self._toolbar.addAction(_action("toolbar.clear_log",        "clear",   self._clear_log))

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._toolbar.addWidget(spacer)

        self.token_status_label = QLabel()
        self.token_status_label.setStyleSheet("padding: 0 12px; font-size: 9pt;")
        self._toolbar.addWidget(self.token_status_label)
        self._update_token_status()

    def _retranslate_toolbar(self):
        """Пересоздаёт тулбар с новым языком (тултипы)."""
        self._fill_toolbar()

    def _update_token_status(self):
        if not hasattr(self, 'token_status_label') or not hasattr(self, 'token_input'):
            return
        token = self.token_input.text().strip() if hasattr(self, 'token_input') else ""
        if token:
            self.token_status_label.setText("🔑 " + lang_mgr.get_text("toolbar.token_set"))
            self.token_status_label.setStyleSheet(
                "padding: 0 12px; font-size: 9pt; color: #40a02b; font-weight: 600;")
        else:
            self.token_status_label.setText("🔑 " + lang_mgr.get_text("toolbar.token_not_set"))
            self.token_status_label.setStyleSheet(
                "padding: 0 12px; font-size: 9pt; color: #d20f39; font-weight: 600;")
