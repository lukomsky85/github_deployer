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

QCheckBox { spacing: 8px; color: #4c4f69; font-size: 10pt; }
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
QLabel { color: #4c4f69; }
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

# 🌍 Translations (EN & RU)
TRANSLATIONS = {
    'en': {
        # Main UI
        "app_title": "GitHub Deploy Helper",
        "menu_file": "File",
        "menu_branches": "Branches",
        "menu_settings": "Settings",
        "menu_language": "Language",
        "action_select_project": "Select Project...",
        "action_deploy": "Deploy (F5)",
        "action_exit": "Exit",
        "action_create_branch": "Create Branch...",
        "action_clear_history": "Clear History",
        
        # Tabs
        "tab_deploy": "Deploy",
        "tab_branches": "Branches",
        "tab_gitignore": ".gitignore",
        "tab_settings": "Settings",
        
        # Deploy Tab
        "deploy_tab.repo_profiles_group": "Repository Profiles",
        "deploy_tab.add_profile_tooltip": "Add new repository profile",
        "deploy_tab.edit_profile_tooltip": "Edit selected profile",
        "deploy_tab.delete_profile_tooltip": "Delete selected profile",
        "deploy_tab.project_group": "Project Path",
        "deploy_tab.path_placeholder": "Path to project folder...",
        "deploy_tab.quick_access": "Quick Access",
        "deploy_tab.current_folder": "Current",
        "deploy_tab.desktop": "Desktop",
        "deploy_tab.repository_group": "Repository",
        "deploy_tab.repo_placeholder": "https://github.com/user/repo.git",
        "deploy_tab.branch_label": "Branch:",
        "deploy_tab.refresh_button": "Refresh",
        "deploy_tab.token_group": "Authentication Token",
        "deploy_tab.token_placeholder": "ghp_... or github_pat_...",
        "deploy_tab.paste_button": "Paste",
        "deploy_tab.show_checkbox": "Show",
        "deploy_tab.save_checkbox": "Save token locally",
        "deploy_tab.token_info": "⚠️ Token is stored locally. Keep it secure!",
        "deploy_tab.commit_group": "Commit Message",
        "deploy_tab.commit_label": "Message:",
        "deploy_tab.add_commit_tooltip": "Add to history",
        "deploy_tab.options_group": "Options",
        "deploy_tab.gitignore_check": "Auto-create/update .gitignore",
        "deploy_tab.create_branch_check": "Create branch if not exists",
        "deploy_tab.preview_button": "Preview .gitignore",
        "deploy_tab.log_group": "Operation Log",
        "deploy_tab.clear_log_button": "Clear Log",
        "deploy_tab.save_log_button": "Save Log",
        "deploy_tab.deploy_button": "🚀 Deploy",
        
        # Messages & Status
        "status_ready": "Ready",
        "status_deploying": "Deploying...",
        "messages.no_changes": "No local changes to commit.",
        "messages.deploy_success": "Successfully deployed to {branch}!",
        "messages.deploy_success_message": "All changes pushed to {branch}.",
        "messages.push_rejected": "Push rejected. Check history or conflicts.",
        "messages.auth_error": "Authentication failed. Check your token.",
        "messages.push_error": "Push failed: {error}",
        "messages.critical_error": "Critical error: {error}",
        "messages.secrets_found": "⚠️ Potential secrets detected!",
        "messages.secrets_advice": "💡 Add sensitive files to .gitignore before pushing.",
        "messages.secrets_clean": "✅ No secrets found — proceeding.",
        "messages.auto_fix_done": "🔧 Auto-fixed {count} files in index.",
        "messages.secret_in_history": "🔑 GitHub blocked push due to a secret in history.",
        "messages.secret_allow_hint": "💡 Follow the error link on GitHub and click 'Allow secret'.",
        "messages.push_rejected_pull": "Push rejected. Perform Pull first.",
        
        # Dialogs & Misc
        "dlg_create_branch": "Create Branch",
        "dlg_branch_name": "Branch Name:",
        "btn_ok": "OK",
        "btn_cancel": "Cancel",
        "btn_browse": "Browse",
        "group_project": "Project Path",
        "group_repo": "Repository",
        "label_url": "URL:",
        "label_branch": "Branch:",
        "btn_refresh": "Refresh",
        "group_token": "Authentication Token",
        "btn_paste": "Paste",
        "group_commit": "Commit Message",
        "check_gitignore": "Auto-update .gitignore",
        "group_log": "Operation Log",
        "btn_deploy": "Deploy",
        "msg_git_missing": "Git is not installed!",
        "msg_no_changes": "No changes to commit.",
        "msg_success": "Success",
        "msg_error": "Error",
        "msg_auth_failed": "Authentication failed.",
        "msg_rejected": "Push rejected. Pull first."
    },
    'ru': {
        # Main UI
        "app_title": "GitHub Deploy Helper",
        "menu_file": "Файл",
        "menu_branches": "Ветки",
        "menu_settings": "Настройки",
        "menu_language": "Язык",
        "action_select_project": "Выбрать проект...",
        "action_deploy": "Деплой (F5)",
        "action_exit": "Выход",
        "action_create_branch": "Создать ветку...",
        "action_clear_history": "Очистить историю",
        
        # Tabs
        "tab_deploy": "Деплой",
        "tab_branches": "Ветки",
        "tab_gitignore": ".gitignore",
        "tab_settings": "Настройки",
        
        # Deploy Tab
        "deploy_tab.repo_profiles_group": "Профили репозиториев",
        "deploy_tab.add_profile_tooltip": "Добавить новый профиль",
        "deploy_tab.edit_profile_tooltip": "Редактировать выбранный профиль",
        "deploy_tab.delete_profile_tooltip": "Удалить выбранный профиль",
        "deploy_tab.project_group": "Путь к проекту",
        "deploy_tab.path_placeholder": "Путь к папке проекта...",
        "deploy_tab.quick_access": "Быстрый доступ",
        "deploy_tab.current_folder": "Текущая",
        "deploy_tab.desktop": "Рабочий стол",
        "deploy_tab.repository_group": "Репозиторий",
        "deploy_tab.repo_placeholder": "https://github.com/user/repo.git",
        "deploy_tab.branch_label": "Ветка:",
        "deploy_tab.refresh_button": "Обновить",
        "deploy_tab.token_group": "Токен доступа",
        "deploy_tab.token_placeholder": "ghp_... или github_pat_...",
        "deploy_tab.paste_button": "Вставить",
        "deploy_tab.show_checkbox": "Показать",
        "deploy_tab.save_checkbox": "Сохранить токен локально",
        "deploy_tab.token_info": "⚠️ Токен хранится локально. Берегите его!",
        "deploy_tab.commit_group": "Сообщение коммита",
        "deploy_tab.commit_label": "Сообщение:",
        "deploy_tab.add_commit_tooltip": "Добавить в историю",
        "deploy_tab.options_group": "Опции",
        "deploy_tab.gitignore_check": "Авто-создание/обновление .gitignore",
        "deploy_tab.create_branch_check": "Создать ветку, если нет",
        "deploy_tab.preview_button": "Предпросмотр .gitignore",
        "deploy_tab.log_group": "Журнал операций",
        "deploy_tab.clear_log_button": "Очистить лог",
        "deploy_tab.save_log_button": "Сохранить лог",
        "deploy_tab.deploy_button": "🚀 Деплой",
        
        # Messages & Status
        "status_ready": "Готово",
        "status_deploying": "Выполняется деплой...",
        "messages.no_changes": "Нет локальных изменений для коммита.",
        "messages.deploy_success": "Успешно отправлено в ветку {branch}!",
        "messages.deploy_success_message": "Все изменения отправлены в {branch}.",
        "messages.push_rejected": "Push отклонён. Проверьте историю или конфликты.",
        "messages.auth_error": "Ошибка авторизации. Проверьте токен.",
        "messages.push_error": "Ошибка пуша: {error}",
        "messages.critical_error": "Критическая ошибка: {error}",
        "messages.secrets_found": "⚠️ Обнаружены потенциальные секреты!",
        "messages.secrets_advice": "💡 Добавьте чувствительные файлы в .gitignore перед пушем.",
        "messages.secrets_clean": "✅ Секреты не обнаружены — продолжаем.",
        "messages.auto_fix_done": "🔧 Автоматически исправлено {count} файлов в индексе.",
        "messages.secret_in_history": "🔑 GitHub заблокировал пуш из-за секрета в истории.",
        "messages.secret_allow_hint": "💡 Перейдите по ссылке в ошибке на GitHub и нажмите 'Allow secret'.",
        "messages.push_rejected_pull": "Push отклонён. Сначала выполните Pull.",
        
        # Dialogs & Misc
        "dlg_create_branch": "Создать ветку",
        "dlg_branch_name": "Имя ветки:",
        "btn_ok": "ОК",
        "btn_cancel": "Отмена",
        "btn_browse": "Обзор",
        "group_project": "Путь к проекту",
        "group_repo": "Репозиторий",
        "label_url": "URL:",
        "label_branch": "Ветка:",
        "btn_refresh": "Обновить",
        "group_token": "Токен доступа",
        "btn_paste": "Вставить",
        "group_commit": "Сообщение коммита",
        "check_gitignore": "Авто-обновление .gitignore",
        "group_log": "Журнал операций",
        "btn_deploy": "Деплой",
        "msg_git_missing": "Git не установлен!",
        "msg_no_changes": "Нет изменений для коммита.",
        "msg_success": "Успех",
        "msg_error": "Ошибка",
        "msg_auth_failed": "Ошибка авторизации.",
        "msg_rejected": "Push отклонен. Сначала сделайте Pull."
    }
}