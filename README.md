# 🚀 GitHub Deploy Helper

> A desktop GUI application for deploying projects to GitHub — without touching the terminal.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green?logo=qt&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![Version](https://img.shields.io/badge/Version-3.0-orange)

---

## ✨ Features

- **One-click deploy** — init repo, commit, and push in a single action
- **Repository profiles** — save multiple project/repo configurations and switch between them
- **Branch management** — create, switch, merge, and delete branches from the UI
- **Auto pull-rebase** — automatically resolves non-fast-forward push rejections
- **Token management** — encrypted storage of your GitHub Personal Access Token
- **Auto `.gitignore`** — generates a sensible `.gitignore` on first deploy
- **Operation log** — timestamped, color-coded log with save to file
- **Multilingual** — English and Russian UI (switchable at runtime)
- **SVG icon system** — clean Feather-style icons, color-aware (white on primary buttons, red on delete)

---

## 📋 Requirements

- Python 3.8 or higher
- Git installed and available in `PATH`
- A GitHub account with a [Personal Access Token](https://github.com/settings/tokens)

---

## ⚙️ Installation

**1. Clone or download the project**

```bash
git clone https://github.com/lukomsky85/github-deploy-helper.git
cd github-deploy-helper
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

> `requirements.txt` contains:
> ```
> PyQt5>=5.15.0
> cryptography>=41.0.0
> ```

**3. Run the app**

```bash
python main.py
```

On Windows you can also double-click `main.py` if Python is associated with `.py` files, or run:

```bash
py main.py
```

---

## 🔑 GitHub Token Setup

GitHub requires a Personal Access Token (PAT) instead of a password for HTTPS push.

1. Go to [github.com/settings/tokens](https://github.com/settings/tokens)
2. Click **Generate new token (classic)**
3. Select scopes: ✅ `repo` (full control of private repositories)
4. Copy the generated token
5. Paste it into the **Authentication Token** field in the app

The token is stored locally in encrypted form using the `cryptography` library.

---

## 🚀 How to Deploy

1. **Select your project folder** — use the Browse button or type the path directly
2. **Enter the repository URL** — e.g. `https://github.com/username/repo.git`
3. **Choose a branch** — `main`, `develop`, or type a custom name
4. **Paste your token** — click Paste or type it in
5. **Write a commit message** — or use one from history
6. **Click Deploy** — the app will:
   - Initialize git if needed
   - Create/update `.gitignore`
   - Stage all changes (`git add -A`)
   - Commit with your message
   - Push to the remote branch
   - Auto-rebase if the push is rejected

---

## 📁 Project Structure

```
proj/
├── main.py                  # Entry point
├── config.py                # Stylesheet, colors, default gitignore
├── requirements.txt
│
├── icons/
│   ├── actions/             # UI action icons (SVG, Feather-style)
│   ├── status/              # Log status icons (success, warning, error, info)
│   └── app/                 # App logo
│
├── languages/
│   ├── en.json              # English translations
│   └── ru.json              # Russian translations
│
├── ui/
│   ├── main_window.py       # Main application window
│   ├── deploy_tab.py        # Deploy tab
│   ├── branches_tab.py      # Branch management tab
│   ├── gitignore_tab.py     # .gitignore editor tab
│   ├── settings_tab.py      # Settings tab
│   ├── about_tab.py         # About tab
│   ├── toolbar.py           # Toolbar
│   ├── menu.py              # Menu bar
│   ├── helpers.py           # Shared UI helpers (log, dialogs, etc.)
│   ├── dialogs.py           # Custom dialog windows
│   └── deploy_thread.py     # Background deploy thread
│
└── utils/
    ├── git_helper.py        # Git command wrapper
    ├── icon_manager.py      # SVG icon loader with colorization
    ├── lang_manager.py      # Language/translation manager
    ├── repo_manager.py      # Repository profile persistence
    ├── crypto.py            # Token encryption/decryption
    ├── history.py           # Commit message history
    └── gitignore.py         # .gitignore utilities
```

---

## 🌍 Changing Language

Go to **File → Language** and select English or Русский. The UI rebuilds instantly without restarting.

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---|---|
| `Git is not installed` | Install Git from [git-scm.com](https://git-scm.com) and make sure it's in your `PATH` |
| `Authentication failed` | Check your token — it must have `repo` scope and not be expired |
| `Push rejected` | The app will auto-rebase; if it fails, pull and resolve conflicts manually |
| `No module named 'PyQt5'` | Run `pip install PyQt5` |
| `No module named 'cryptography'` | Run `pip install cryptography` |
| Icons not showing | Make sure the `icons/` folder is in the same directory as `main.py` |

---

## 📄 License

MIT License — use freely, modify freely, no warranty.
