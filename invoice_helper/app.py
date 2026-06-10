"""
开票待办助手 - Flask主应用
"""
import os
import sys
from flask import Flask, render_template, send_from_directory

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from models import init_db
from routes import customers_bp, todos_bp, settings_bp, files_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'invoice-helper-secret-key'

# 注册路由
app.register_blueprint(customers_bp)
app.register_blueprint(todos_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(files_bp)


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
    """静态文件"""
    return send_from_directory('static', filename)


if __name__ == '__main__':
    # 初始化数据库
    init_db()
    
    # 启动服务
    print('开票待办助手启动中...')
    print('请在浏览器访问: http://127.0.0.1:5000')
    app.run(host='127.0.0.1', port=5000, debug=False)