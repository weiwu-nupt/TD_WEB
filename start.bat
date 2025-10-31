@echo off
chcp 65001 >nul
echo ========================================
echo 正在启动地面检测系统...
echo ========================================


REM 启动后端 (在新窗口)
echo 启动后端服务...
start "后端服务 - Python" cmd /k "cd /d %~dp0backend && python main.py"

REM 等待2秒
timeout /t 2 /nobreak >nul

REM 启动前端 (在新窗口)
echo 启动前端服务...
start "前端服务 - Vue" cmd /k "cd /d %~dp0frontend && npm run dev"

