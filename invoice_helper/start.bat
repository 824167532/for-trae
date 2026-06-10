@echo off
chcp 65001 >nul
title 开票待办助手

echo ========================================
echo   开票待办助手启动程序
echo ========================================
echo.

cd /d "%~dp0"

echo 正在检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python环境，请先安装Python 3.8或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo 正在检查依赖...
pip show Flask >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

echo 正在启动服务...
echo.
echo 请在浏览器访问: http://127.0.0.1:5000
echo 按 Ctrl+C 可停止服务
echo.

python app.py

pause