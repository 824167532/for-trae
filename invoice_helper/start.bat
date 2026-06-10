@echo off
chcp 65001 >nul
title 开票待办助手

echo ========================================
echo   开票待办助手 - Windows启动程序
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python环境
    echo.
    echo 请先安装Python 3.8或更高版本
    echo 下载地址: https://www.python.org/downloads/
    echo.
    echo 安装时请务必勾选 "Add Python to PATH"
    pause
    exit /b 1
)
echo [OK] Python环境检测通过
echo.

echo [2/3] 检查依赖包...
pip show Flask >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖包（可能需要几分钟）...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [错误] 依赖安装失败，请检查网络连接
        echo 或手动执行: pip install Flask openpyxl
        pause
        exit /b 1
    )
    echo [OK] 依赖安装完成
) else (
    echo [OK] 依赖已安装
)
echo.

echo [3/3] 启动服务...
echo.
echo ========================================
echo   服务已启动
echo ========================================
echo.
echo 请在浏览器中访问: http://127.0.0.1:5000
echo.
echo 提示:
echo   1. 首次访问会自动打开浏览器
echo   2. 如未自动打开，请手动访问上述地址
echo   3. 按 Ctrl+C 可停止服务
echo   4. 请勿关闭此窗口，关闭窗口会停止服务
echo.
echo ========================================
echo.

python app.py

pause
