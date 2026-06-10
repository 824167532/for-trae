"""
数据模型定义
"""
import sqlite3
import os
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'invoice_helper.db')


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库"""
    # 确保data目录存在
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 创建客户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            display_name TEXT NOT NULL UNIQUE,
            relative_path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建待办表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            business_month TEXT NOT NULL,
            amount DECIMAL(10, 2),
            invoice_status TEXT DEFAULT 'pending',
            send_status TEXT DEFAULT 'unsent',
            sent_at TIMESTAMP,
            screenshot_filename TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
        )
    ''')
    
    # 创建设置表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL UNIQUE,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建索引
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_todos_customer_month 
        ON todos(customer_id, business_month)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_todos_status 
        ON todos(invoice_status, send_status)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_todos_created 
        ON todos(created_at)
    ''')
    
    # 初始设置
    cursor.execute('''
        INSERT OR IGNORE INTO settings (key, value) VALUES ('root_directory', '')
    ''')
    
    conn.commit()
    conn.close()


# 初始化数据库
init_db()