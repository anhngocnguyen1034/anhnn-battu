@echo off
chcp 65001 >nul 2>&1
title FOR-BAZI · 玄冥 Cyber-Bazi

echo ========================================
echo   FOR-BAZI · 玄冥 Cyber-Bazi
echo   专业八字命理 AI 系统
echo ========================================
echo.

REM Get the directory where this script lives
set "APP_DIR=%~dp0"

REM Start backend (hidden window)
echo [1/3] 启动后端服务...
start /b "" "%APP_DIR%bazi-backend\bazi-backend.exe" --host 127.0.0.1 --port 8000 >nul 2>&1

REM Wait for backend to be ready
echo [2/3] 等待后端就绪...
set READY=0
for /L %%i in (1,1,30) do (
    if !READY! equ 0 (
        curl -s http://127.0.0.1:8000/health >nul 2>&1 && set READY=1
        if !READY! equ 0 timeout /t 1 /nobreak >nul
    )
)

if %READY% equ 0 (
    echo [错误] 后端启动超时，请检查 bazi-backend 目录
    pause
    exit /b 1
)

echo [3/3] 启动应用界面...
start "" "%APP_DIR%FOR-BAZI.exe"

echo.
echo 应用已启动！关闭此窗口将停止后端服务。
echo.
echo 按任意键停止后端并退出...
pause >nul

REM Kill backend process
taskkill /im bazi-backend.exe /f >nul 2>&1
