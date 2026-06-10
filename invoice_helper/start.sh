#!/bin/bash

# 开票待办助手 - macOS启动脚本
echo "========================================"
echo "  开票待办助手启动程序"
echo "========================================"
echo ""

# 切换到脚本所在目录
cd "$(dirname "$0")"

echo "正在检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到Python 3环境，请先安装Python 3.8或更高版本"
    echo "下载地址: https://www.python.org/downloads/"
    exit 1
fi

echo "正在检查依赖..."
if ! python3 -c "import flask" &> /dev/null; then
    echo "正在安装依赖..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[错误] 依赖安装失败"
        exit 1
    fi
fi

echo "正在启动服务..."
echo ""
echo "请在浏览器访问: http://127.0.0.1:5000"
echo "按 Ctrl+C 可停止服务"
echo ""

python3 app.py
