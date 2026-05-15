# ui/toolbar.py
from PyQt5.QtWidgets import QToolBar, QAction, QWidget, QLabel, QSizePolicy
from PyQt5.QtCore import QSize

from utils.lang_manager import lang_mgr
from utils.icon_manager import IconManager


class ToolbarMixin:

    def _setup_toolbar(self):
        self._icons = IconManager()

        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(18, 18))
        toolbar.setToolButtonStyle(2)  # TextBesideIcon
        self.addToolBar(toolbar)

        def _action(text_key, icon_name, slot, shortcut=None):
            act = QAction(lang_mgr.get_text(text_key), self)
            self._icons.set_action_icon(act, icon_name, size=QSize(18, 18))
            act.triggered.connect(slot)
            if shortcut:
                act.setShortcut(shortcut)
            return act

        toolbar.addAction(_action("toolbar.deploy",          "deploy",  self.start_deployment, "F5"))
        toolbar.addSeparator()
        toolbar.addAction(_action("toolbar.refresh_branches","refresh", self._refresh_branches))
        toolbar.addSeparator()
        toolbar.addAction(_action("toolbar.clear_log",       "clear",   self._clear_log))

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)

        self.token_status_label = QLabel()
        self.token_status_label.setStyleSheet("padding: 0 12px; font-size: 9pt;")
        toolbar.addWidget(self.token_status_label)
        self._update_token_status()

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
