# ui/toolbar.py
from PyQt5.QtWidgets import (
    QToolBar, QAction, QWidget, QLabel, QSizePolicy
)
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QFont

from utils.lang_manager import lang_mgr


class ToolbarMixin:
    """Mixin для тулбара"""

    def _setup_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setToolButtonStyle(2)  # ToolButtonTextBesideIcon → fallback: text only
        self.addToolBar(toolbar)

        deploy_action = QAction("Deploy", self)
        deploy_action.setToolTip(lang_mgr.get_text("toolbar.deploy"))
        deploy_action.triggered.connect(self.start_deployment)
        toolbar.addAction(deploy_action)

        toolbar.addSeparator()

        refresh_action = QAction("Refresh Branches", self)
        refresh_action.setToolTip(lang_mgr.get_text("toolbar.refresh_branches"))
        refresh_action.triggered.connect(self._refresh_branches)
        toolbar.addAction(refresh_action)

        toolbar.addSeparator()

        clear_action = QAction("Clear Log", self)
        clear_action.setToolTip(lang_mgr.get_text("toolbar.clear_log"))
        clear_action.triggered.connect(self._clear_log)
        toolbar.addAction(clear_action)

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
        token = self.token_input.text().strip()
        if token:
            self.token_status_label.setText("Token: set")
            self.token_status_label.setStyleSheet(
                "padding: 0 12px; font-size: 9pt; color: #40a02b; font-weight: 600;")
        else:
            self.token_status_label.setText("Token: not set")
            self.token_status_label.setStyleSheet(
                "padding: 0 12px; font-size: 9pt; color: #d20f39; font-weight: 600;")
