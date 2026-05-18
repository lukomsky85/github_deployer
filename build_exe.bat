@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ╔════════════════════════════════════════════════════════════╗
echo ║   GitHub Deploy Helper — Сборка в EXE                    ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM ============================================================================
REM 1. ПРОВЕРКА PYTHON
REM ============================================================================
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python не найден в PATH!
    echo 💡 Установите Python и отметьте галочку "Add Python to PATH"
    pause
    exit /b 1
)
echo ✅ Python: 
python --version

REM ============================================================================
REM 2. ПРОВЕРКА / УСТАНОВКА PYINSTALLER
REM ============================================================================
echo.
echo 🔍 Проверка PyInstaller...
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo ⬇️  PyInstaller не найден. Устанавливаю...
    python -m pip install pyinstaller --quiet
    if %errorlevel% neq 0 (
        echo ❌ Не удалось установить PyInstaller
        pause
        exit /b 1
    )
    echo ✅ PyInstaller установлен
) else (
    echo ✅ PyInstaller найден
)

REM ============================================================================
REM 3. ОЧИСТКА СТАРЫХ АРТЕФАКТОВ
REM ============================================================================
echo.
echo 🧹 Очистка временных файлов сборки...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "GitHub_Deploy_Helper.spec" del /q "GitHub_Deploy_Helper.spec"

REM ============================================================================
REM 4. ЗАПУСК СБОРКИ
REM ============================================================================
echo.
echo 🔨 Запуск PyInstaller...
echo ────────────────────────────────────────────────────────────

pyinstaller ^
    --name "GitHub_Deploy_Helper" ^
    --onefile ^
    --windowed ^
    --clean ^
    --log-level=INFO ^
    --hidden-import=PyQt5.sip ^
    --hidden-import=PyQt5.QtCore ^
    --hidden-import=PyQt5.QtGui ^
    --hidden-import=PyQt5.QtWidgets ^
    --hidden-import=cryptography.fernet ^
    --hidden-import=utils.crypto ^
    --hidden-import=utils.history ^
    --hidden-import=utils.git_helper ^
    --hidden-import=utils.gitignore ^
    --hidden-import=utils.lang_manager ^
    --hidden-import=utils.repo_manager ^
    --hidden-import=ui.deploy_thread ^
    --hidden-import=ui.deploy_tab ^
    --hidden-import=ui.branches_tab ^
    --hidden-import=ui.gitignore_tab ^
    --hidden-import=ui.settings_tab ^
    --hidden-import=ui.about_tab ^
    --hidden-import=ui.toolbar ^
    --hidden-import=ui.menu ^
    --hidden-import=ui.helpers ^
    --hidden-import=ui.dialogs ^
    --hidden-import=ui.graph_widget ^
    --hidden-import=utils.icon_manager ^
    --add-data "languages;languages" ^
    --add-data "icons;icons" ^
    main.py

set BUILD_RESULT=%errorlevel%
echo ────────────────────────────────────────────────────────────

REM ============================================================================
REM 5. РЕЗУЛЬТАТ
REM ============================================================================
echo.
if %BUILD_RESULT% equ 0 (
    echo ✅ Сборка завершена успешно!
    echo.
    echo 📁 Готовый файл: dist\GitHub_Deploy_Helper.exe
    echo 📏 Размер: ~50-80 MB (норма для PyQt5 + Python runtime)
    echo.
    choice /C YN /M "📂 Открыть папку с готовым EXE? (Y/N)"
    if !errorlevel! equ 1 explorer "%CD%\dist"
) else (
    echo ❌ Ошибка сборки (код: %BUILD_RESULT%)
    echo.
    echo 💡 Возможные причины:
    echo    • Синтаксическая ошибка в коде
    echo    • Отсутствие файла/папки (например, languages/, icons/)
    echo    • Антивирус блокирует создание файлов
    echo.
    echo 🔍 Подробный лог находится в папке: build\GitHub_Deploy_Helper\
)

echo.
pause
endlocal