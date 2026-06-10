"""
开票待办助手 - Flask主应用
支持Windows和macOS双平台
版本号的唯一真源是 version.json，通过 version_utils.py 读取
"""
import os
import sys
import platform
import webbrowser
from threading import Timer

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, send_from_directory, jsonify
from version_utils import get_version, get_version_name, get_release_date
from routes.customers import customers_bp
from routes.todos import todos_bp
from routes.settings import settings_bp
from routes.files import files_bp
from routes.scan import scan_bp

# 初始化Flask应用
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config['SECRET_KEY'] = 'invoice-helper-secret-key-' + str(os.getpid())

# 注册蓝图
app.register_blueprint(customers_bp)
app.register_blueprint(todos_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(files_bp)
app.register_blueprint(scan_bp)


@app.context_processor
def inject_version():
    """注入版本号到所有模板（用于CSS/JS缓存清除）"""
    return {'app_version': get_version()}


@app.route('/api/version')
def get_api_version():
    """返回版本信息API"""
    from version_utils import get_version_info
    return jsonify(get_version_info())


@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')


@app.route('/history')
def history():
    """历史记录页面"""
    return render_template('history.html')


@app.route('/settings')
def settings():
    """设置页面"""
    return render_template('settings.html')


@app.route('/static/<path:filename>')
def static_files(filename):
    """静态文件服务"""
    return send_from_directory('static', filename)


def get_system_info():
    """获取系统信息"""
    system = platform.system()
    release = platform.release()
    
    if system == 'Darwin':
        return f"macOS {release}"
    elif system == 'Windows':
        return f"Windows {release}"
    elif system == 'Linux':
        return f"Linux {release}"
    else:
        return system


def open_browser():
    """自动打开浏览器"""
    url = 'http://127.0.0.1:5000'
    try:
        webbrowser.open(url)
    except Exception:
        pass


if __name__ == '__main__':
    # 初始化数据库
    from models import init_db
    init_db()
    
    # 获取系统信息和版本信息
    system_info = get_system_info()
    version_str = get_version()
    version_name = get_version_name()
    release_date = get_release_date()
    
    # 启动信息
    print("=" * 50)
    print(f"        {version_name}")
    print(f"        版本: {version_str}")
    print(f"        发布日期: {release_date}")
    print("=" * 50)
    print(f"系统平台: {system_info}")
    print(f"Python版本: {platform.python_version()}")
    print(f"服务地址: http://127.0.0.1:5000")
    print(f"项目根目录: {os.path.dirname(os.path.abspath(__file__))}")
    print("=" * 50)
    print("按 Ctrl+C 可停止服务")
    print("=" * 50)
    print()
    
    # 延迟1秒后自动打开浏览器
    Timer(1.0, open_browser).start()
    
    # 启动服务
    # Windows和macOS都使用默认设置
    app.run(host='127.0.0.1', port=5000, debug=False)
