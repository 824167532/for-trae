#!/bin/bash
# 开票待办助手 - macOS 双击启动脚本
# 双击此文件即可直接运行

cd "$(dirname "$0")"

echo "========================================"
echo "  开票待办助手 - macOS启动程序"
echo "========================================"
echo

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到Python 3环境"
    echo
    echo "请先安装Python 3.8或更高版本"
    echo "下载地址: https://www.python.org/downloads/"
    echo
    read -p "按回车键退出..."
    exit 1
fi
echo "[OK] Python环境检测通过"
echo

# 检查依赖
pip3 show Flask > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "正在安装依赖包..."
    pip3 install -q flask openpyxl
    echo "[OK] 依赖安装完成"
fi
echo

echo "启动服务..."
echo
echo "========================================"
echo "  服务已启动"
echo "========================================"
echo
echo "请在浏览器中访问: http://127.0.0.1:5000"
echo
echo "提示:"
echo "  1. 首次访问会自动打开浏览器"
echo "  2. 按 Ctrl+C 可停止服务"
echo "  3. 关闭此窗口会停止服务"
echo
echo "========================================"
echo

python3 app.py

read -p "按回车键退出..."