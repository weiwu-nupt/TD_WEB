@echo off
chcp 65001 >nul
echo ========================================
echo ��������������ϵͳ...
echo ========================================


REM ������� (���´���)
echo ������˷���...
start "��˷��� - Python" cmd /k "cd /d %~dp0backend && python main.py"

REM �ȴ�2��
timeout /t 2 /nobreak >nul

REM ����ǰ�� (���´���)
echo ����ǰ�˷���...
start "ǰ�˷��� - Vue" cmd /k "cd /d %~dp0frontend && npm run dev"

