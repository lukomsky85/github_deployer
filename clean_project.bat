@echo off
chcp 65001 >nul
title 🧹 Очистка проекта GitHub Deploy Helper
echo ╔════════════════════════════════════════════════════════════╗
echo ║  🧹 Очистка временных и сборочных файлов                   ║
echo ════════════════════════════════════════════════════════════╝
echo.

echo ⚠️  Скрипт удалит кэш Python, папки сборки PyInstaller и runtime-данные.
echo    Исходный код и папки utils/, ui/, languages/ будут сохранены.
echo.
choice /C YN /M "Продолжить очистку? (Y/N)"
if errorlevel 2 goto :EOF

echo 🧹 Удаление __pycache__ и .pyc файлов...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q *.pyc >nul 2>&1
del /s /q *.pyo >nul 2>&1

echo 🧹 Удаление папок сборки PyInstaller...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "*.spec" del /q *.spec

echo 🧹 Удаление временных файлов IDE и ОС...
if exist ".vscode" rmdir /s /q .vscode
if exist ".idea" rmdir /s /q .idea
del /s /q *.log >nul 2>&1
del /s /q *.tmp >nul 2>&1

echo 🧹 Удаление runtime-данных (создаются автоматически при запуске)...
if exist "secure_token.dat" del /q secure_token.dat
if exist "commit_history.json" del /q commit_history.json
if exist "repositories.json" del /q repositories.json

echo ✅ Очистка завершена!
echo.
echo 📦 Проект готов к упаковке или коммиту.
pause