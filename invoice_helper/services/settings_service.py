"""
设置服务
"""
from datetime import datetime
from models import get_db_connection


class SettingsService:
    """设置服务类"""
    
    def get_all(self):
        """获取所有设置"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM settings')
        rows = cursor.fetchall()
        conn.close()
        return {row['key']: row['value'] for row in rows}
    
    def get(self, key):
        """获取单个设置"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        conn.close()
        return row['value'] if row else None
    
    def set(self, key, value):
        """设置值"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)',
            (key, value, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
        return True
    
    def get_root_directory(self):
        """获取根目录"""
        return self.get('root_directory') or ''
    
    def set_root_directory(self, path):
        """设置根目录"""
        return self.set('root_directory', path)