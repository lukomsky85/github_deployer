# config.py
import os

# 🎨 Colors — Catppuccin Latte (Light Theme)
COLORS = {
    'bg':           '#eff1f5',
    'bg_secondary': '#e6e9ef',
    'bg_card':      '#ffffff',
    'text':         '#4c4f69',
    'text_muted':   '#8c8fa1',
    'accent':       '#1e66f5',
    'accent_dark':  '#1554d4',
    'success':      '#40a02b',
    'warning':      '#df8e1d',
    'error':        '#d20f39',
    'button_bg':    '#dce0e8',
    'button_hover': '#ccd0da',
    'border':       '#ccd0da',
}

# 🖌️ Global Stylesheet
STYLESHEET = """
QMainWindow, QWidget {
    background-color: #eff1f5;
    color: #4c4f69;
    font-family: "Segoe UI", "Inter", system-ui, sans-serif;
    font-size: 10pt;
}

QMenuBar {
    background-color: #e6e9ef;
    color: #4c4f69;
    border-bottom: 1px solid #ccd0da;
    padding: 2px 0;
}
QMenuBar::item {
    padding: 6px 14px;
    border-radius: 4px;
    background: transparent;
}
QMenuBar::item:selected, QMenuBar::item:pressed {
    background-color: #ccd0da;
    color: #1e66f5;
}
QMenu {
    background-color: #ffffff;
    color: #4c4f69;
    border: 1px solid #ccd0da;
    border-radius: 8px;
    padding: 4px;
}
QMenu::item {
    padding: 7px 20px 7px 12px;
    border-radius: 5px;
}
QMenu::item:selected {
    background-color: #e6e9ef;
    color: #1e66f5;
}
QMenu::separator {
    height: 1px;
    background: #e6e9ef;
    margin: 3px 8px;
}

QToolBar {
    background-color: #e6e9ef;
    border-bottom: 1px solid #ccd0da;
    padding: 4px 8px;
    spacing: 6px;
}
QToolBar QToolButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 6px;
    color: #4c4f69;
    font-size: 16px;
}
QToolBar QToolButton:hover {
    background-color: #dce0e8;
    border-color: #ccd0da;
}
QToolBar QToolButton:pressed {
    background-color: #ccd0da;
}
QToolBar::separator {
    width: 1px;
    background: #ccd0da;
    margin: 4px 6px;
}

QStatusBar {
    background-color: #e6e9ef;
    color: #4c4f69;
    border-top: 1px solid #ccd0da;
    padding: 2px 8px;
    font-size: 9pt;
}
QStatusBar::item { border: none; }

QTabWidget::pane {
    border: 1px solid #ccd0da;
    border-radius: 8px;
    background-color: #ffffff;
    top: -1px;
}
QTabBar { background: transparent; }
QTabBar::tab {
    background-color: #e6e9ef;
    color: #6c6f85;
    border: 1px solid #ccd0da;
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    padding: 8px 18px;
    margin-right: 3px;
    font-weight: 500;
}
QTabBar::tab:hover {
    background-color: #dce0e8;
    color: #4c4f69;
}
QTabBar::tab:selected {
    background-color: #1e66f5;
    color: #ffffff;
    border-color: #1e66f5;
    font-weight: 600;
}

QPushButton {
    background-color: #dce0e8;
    color: #4c4f69;
    border: 1px solid #ccd0da;
    border-radius: 7px;
    padding: 7px 16px;
    font-weight: 500;
    font-size: 10pt;
    min-height: 24px;
}
QPushButton:hover {
    background-color: #ccd0da;
    border-color: #acb0be;
    color: #1e66f5;
}
QPushButton:pressed {
    background-color: #bcc0cc;
}
QPushButton:disabled {
    background-color: #e6e9ef;
    color: #a0a3b1;
    border-color: #dce0e8;
}
QPushButton:focus { outline: none; border-color: #1e66f5; }

QLineEdit, QTextEdit, QComboBox, QPlainTextEdit {
    background-color: #ffffff;
    color: #4c4f69;
    border: 1.5px solid #ccd0da;
    border-radius: 7px;
    padding: 7px 10px;
    selection-background-color: #1e66f5;
    selection-color: #ffffff;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #1e66f5;
}
QLineEdit:hover, QComboBox:hover { border-color: #acb0be; }

QComboBox { padding-right: 28px; min-height: 24px; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #ccd0da;
    border-radius: 6px;
    padding: 3px;
    selection-background-color: #e6e9ef;
    selection-color: #1e66f5;
    outline: none;
}
QComboBox QAbstractItemView::item {
    padding: 6px 10px;
    border-radius: 4px;
    min-height: 22px;
}

QGroupBox {
    background-color: #ffffff;
    border: 1px solid #dce0e8;
    border-radius: 10px;
    margin-top: 14px;
    padding: 16px 12px 12px 12px;
    font-weight: 600;
    color: #4c4f69;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    top: 0px;
    padding: 0 6px;
    background-color: #eff1f5;
    color: #4c4f69;
    border-radius: 4px;
    font-size: 9.5pt;
    font-weight: 600;
}

QCheckBox {
    spacing: 8px;
    color: #4c4f69;
    font-size: 10pt;
    background: transparent;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #ccd0da;
    border-radius: 5px;
    background-color: #ffffff;
}
QCheckBox::indicator:hover { border-color: #1e66f5; }
QCheckBox::indicator:checked {
    background-color: #1e66f5;
    border-color: #1e66f5;
}

QGroupBox QWidget {
    background: transparent;
}
QGroupBox QCheckBox {
    background: transparent;
}
QGroupBox QLabel {
    background: transparent;
}
QGroupBox QRadioButton {
    background: transparent;
}
QScrollArea QWidget {
    background: transparent;
}

QScrollBar:vertical {
    background: #f0f0f0;
    width: 8px;
    border-radius: 4px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #ccd0da;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #acb0be; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #f0f0f0;
    height: 8px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #ccd0da;
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover { background: #acb0be; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

QTreeWidget {
    background-color: #ffffff;
    border: 1px solid #dce0e8;
    border-radius: 8px;
    padding: 4px;
    alternate-background-color: #f8f9fc;
    outline: none;
}
QTreeWidget::item { padding: 5px 8px; border-radius: 5px; }
QTreeWidget::item:hover { background-color: #f0f4ff; }
QTreeWidget::item:selected { background-color: #dbeafe; color: #1e66f5; }

QHeaderView::section {
    background-color: #e6e9ef;
    color: #6c6f85;
    border: none;
    border-right: 1px solid #dce0e8;
    border-bottom: 1px solid #dce0e8;
    padding: 6px 10px;
    font-weight: 600;
    font-size: 9.5pt;
}

QProgressBar {
    background-color: #e6e9ef;
    border: 1px solid #ccd0da;
    border-radius: 5px;
    height: 8px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1e66f5, stop:1 #4f8ef7);
    border-radius: 4px;
}

QScrollArea { background: transparent; border: none; }
QScrollArea > QWidget > QWidget { background: transparent; }
QLabel { color: #4c4f69; background: transparent; }

QSpinBox {
    background-color: #ffffff;
    color: #4c4f69;
    border: 1.5px solid #ccd0da;
    border-radius: 7px;
    padding: 5px 8px;
    selection-background-color: #1e66f5;
}
QSpinBox:focus {
    border-color: #1e66f5;
}
QSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 20px;
    border-left: 1px solid #ccd0da;
    border-bottom: 1px solid #ccd0da;
    border-top-right-radius: 6px;
    background: #e6e9ef;
}
QSpinBox::up-button:hover { background: #dce0e8; }
QSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 20px;
    border-left: 1px solid #ccd0da;
    border-top: 1px solid #ccd0da;
    border-bottom-right-radius: 6px;
    background: #e6e9ef;
}
QSpinBox::down-button:hover { background: #dce0e8; }
QSpinBox::up-arrow  { width: 8px; height: 8px; }
QSpinBox::down-arrow { width: 8px; height: 8px; }

"""

# 📁 Default Gitignore Template (Updated & Secure)
DEFAULT_GITIGNORE = """# 🔐 Secrets & Local Configs (CRITICAL)
repositories.json
secure_token.dat
*.env
.env.local
config_local.py
secrets.json
*.key
*.pem

# 🐍 Python
__pycache__/
*.py[cod]
*.pyo
*.so
.Python
venv/
.venv/
env/
*.egg-info/
.eggs/
*.egg

# 📦 PyInstaller / Build
build/
dist/
*.spec
*.manifest
*.exe

# 💻 IDE & OS
.vscode/
.idea/
*.iml
*.ipr
*.iws
.DS_Store
Thumbs.db
Desktop.ini
*.log
*.tmp
"""