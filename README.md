# GitHub Deploy Helper v3.0

> Desktop GUI приложение для деплоя проектов на GitHub — без терминала.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green?logo=qt&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![Version](https://img.shields.io/badge/Version-3.0-orange)

---

## Возможности

- **Деплой одной кнопкой** — init, commit, push за один клик с автоматическим pull-rebase при rejected
- **Профили репозиториев** — сохраняйте несколько конфигураций проект/репозиторий и переключайтесь между ними
- **Групповой деплой** — выберите несколько проектов и запустите деплой все разом
- **Управление ветками** — создание, переключение, слияние, удаление из UI
- **Граф коммитов** — визуальное дерево истории веток с фильтрацией и деталями коммита
- **Автоматизация** — расписание автодеплоя (каждый час, каждый день) и pre/post хуки (тесты, сборка, скрипты)
- **Безопасное хранение токена** — Windows Credential Manager / macOS Keychain / Linux SecretService через `keyring`, fallback на AES-128 Fernet
- **Сканер секретов** — проверка файлов перед пушем на утечку токенов и ключей
- **Авто `.gitignore`** — создаётся автоматически при первом деплое
- **Цветной лог** — журнал операций с временными метками и уровнями
- **Два языка** — English и Русский, переключение без перезапуска

---

## Требования

- Python 3.8+
- Git в `PATH`
- GitHub аккаунт с [Personal Access Token](https://github.com/settings/tokens)

---

## Установка

```bash
# 1. Клонировать или скачать проект
git clone https://github.com/lukomsky85/github-deploy-helper.git
cd github-deploy-helper

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Запустить
python main.py
```

**Windows:**
```bash
py main.py
```

`requirements.txt`:
```
PyQt5>=5.15.0
cryptography>=41.0.0
keyring>=24.0.0
```

---

## GitHub Token

GitHub требует Personal Access Token вместо пароля для HTTPS push.

1. Открыть [github.com/settings/tokens](https://github.com/settings/tokens)
2. **Generate new token (classic)**
3. Выбрать scope: `repo` (полный доступ к репозиториям)
4. Скопировать токен
5. Вставить в поле **GitHub Token** во вкладке Deploy

Токен сохраняется в системном хранилище ОС (Credential Manager / Keychain) — на диск в открытом виде не пишется.

---

## Вкладки

### Deploy — основной деплой
- Выбор проекта и репозитория
- Управление профилями (добавить, изменить, удалить, сохранить)
- Выбор ветки с обновлением списка из remote
- Вставка и безопасное хранение токена
- История сообщений коммита
- Авто `.gitignore`, опция создания новой ветки
- Журнал операций с сохранением в файл

### Branches — ветки
- Список локальных веток с датой последнего коммита
- Переключение на выбранную ветку одним кликом
- Создание, удаление, слияние веток

### .gitignore
- Редактор `.gitignore` с предпросмотром
- Применение к текущему репозиторию

### Settings — настройки
- Информация о хранилище токена (бэкенд, маскированное значение)
- Управление историей коммитов
- Сброс настроек

### Commit Graph — граф коммитов
- Визуальное дерево веток через `QPainter` (Bezier-кривые, цветные дорожки)
- Клик на коммит — детали: SHA, автор, дата, ветки, изменённые файлы
- Фильтрация по сообщению, автору, SHA, ветке
- Настройка максимального числа коммитов (10–2000)
- Синхронизация пути из вкладки Deploy

### Batch Deploy — групповой деплой
- Добавление проектов из сохранённых профилей или папки
- Чекбокс на каждом проекте — включить/отключить без удаления
- Общие параметры: коммит, ветка, токен
- Счётчики: Всего / Успешно / Ошибок / Ожидает
- Прогресс-бар и журнал с временными метками
- Кнопка остановки очереди

### Automation — автоматизация
**Pre/Post хуки:**
- Запуск скриптов до пуша (тесты, линтер, сборка) и после (уведомления, публикация)
- Настройка таймаута и поведения при ошибке (`stop_on_fail`)
- Ручной запуск pre/post хуков без деплоя
- Статус последнего запуска в таблице

**Расписание:**
- Автодеплой через интервалы: 30 мин / 1ч / 2ч / 6ч / 12ч / 24ч
- Привязка к профилю репозитория
- Запуск pre/post хуков в составе расписания
- Журнал со временем следующего запуска

---

## Структура проекта

```
├── main.py                    # Точка входа
├── config.py                  # Stylesheet, цвета
├── requirements.txt
│
├── languages/
│   ├── en.json                # English
│   └── ru.json                # Русский
│
├── icons/
│   ├── actions/               # SVG иконки действий (Feather-style, currentColor)
│   └── status/                # SVG иконки статусов (success, warning, error, info)
│
├── ui/
│   ├── main_window.py         # Главное окно, TAB_DEFS, смена языка
│   ├── deploy_tab.py          # Вкладка Deploy
│   ├── branches_tab.py        # Вкладка Branches
│   ├── gitignore_tab.py       # Вкладка .gitignore
│   ├── settings_tab.py        # Вкладка Settings
│   ├── graph_tab.py           # Вкладка Commit Graph
│   ├── graph_widget.py        # QPainter виджет графа
│   ├── batch_tab.py           # Вкладка Batch Deploy
│   ├── automation_tab.py      # Вкладка Automation (хуки + расписание)
│   ├── about_tab.py           # Вкладка About
│   ├── toolbar.py             # Тулбар (иконки-только, тултипы)
│   ├── menu.py                # Меню с SVG иконками
│   ├── helpers.py             # Общие методы UI
│   ├── dialogs.py             # Диалоговые окна
│   └── deploy_thread.py       # Фоновый поток деплоя
│
└── utils/
    ├── git_helper.py          # Обёртка git команд, сканер секретов
    ├── git_graph.py           # Парсер git log, lane layout алгоритм
    ├── crypto.py              # keyring + Fernet хранение токена
    ├── hooks.py               # Pre/post хуки
    ├── scheduler.py           # Планировщик автодеплоя
    ├── icon_manager.py        # SVG → QIcon с перекраской цвета
    ├── lang_manager.py        # Синглтон локализации с персистентностью
    ├── repo_manager.py        # Профили репозиториев
    ├── history.py             # История сообщений коммита
    └── gitignore.py           # Утилиты .gitignore
```

---

## Файлы данных (создаются автоматически)

| Файл | Описание |
|---|---|
| `settings.json` | Язык, путь к проекту, последняя ветка |
| `repositories.json` | Профили репозиториев |
| `hooks.json` | Pre/post хуки |
| `schedules.json` | Расписания автодеплоя |
| `commit_history.json` | История сообщений коммита |
| `secure_token.dat` | Зашифрованный токен (только если keyring недоступен) |

---

## Устранение проблем

| Проблема | Решение |
|---|---|
| `Git не установлен` | Установить с [git-scm.com](https://git-scm.com), добавить в PATH |
| `Ошибка авторизации` | Проверить токен — нужен scope `repo`, токен не истёк |
| `Push отклонён` | Приложение автоматически делает pull --rebase; при конфликте — разрешить вручную |
| `No module named 'PyQt5'` | `pip install PyQt5` |
| `No module named 'keyring'` | `pip install keyring` (опционально, но рекомендуется) |
| `No module named 'cryptography'` | `pip install cryptography` |
| Иконки не отображаются | Убедиться что папка `icons/` рядом с `main.py` |
| Секреты найдены в файлах | Добавить файл в `.gitignore`, удалить из индекса: `git rm --cached <file>` |

---

## Лицензия

MIT License — используйте свободно, без гарантий.

© 2026 GitHub Deploy Helper
