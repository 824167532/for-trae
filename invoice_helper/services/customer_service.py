"""
客户服务
"""
import sqlite3
from datetime import datetime
from models import get_db_connection


class CustomerService:
    """客户服务类"""
    
    def get_all(self):
        """获取所有客户"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers ORDER BY display_name')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_by_id(self, customer_id):
        """根据ID获取客户"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def create(self, display_name, relative_path):
        """创建客户"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO customers (display_name, relative_path) VALUES (?, ?)',
                (display_name, relative_path)
            )
            conn.commit()
            customer_id = cursor.lastrowid
            conn.close()
            return self.get_by_id(customer_id)
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    def update(self, customer_id, display_name, relative_path):
        """更新客户"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                'UPDATE customers SET display_name = ?, relative_path = ?, updated_at = ? WHERE id = ?',
                (display_name, relative_path, datetime.now().isoformat(), customer_id)
            )
            conn.commit()
            conn.close()
            return self.get_by_id(customer_id)
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    def delete(self, customer_id):
        """删除客户"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM customers WHERE id = ?', (customer_id,))
        conn.commit()
        conn.close()
        return True
    
    def import_from_excel(self, data_list):
        """从Excel数据导入客户"""
        imported_count = 0
        errors = []
        
        for item in data_list:
            display_name = item.get('客户显示名', '').strip()
            relative_path = item.get('相对路径', '').strip()
            
            if not display_name or not relative_path:
                errors.append(f'行数据不完整: {item}')
                continue
            
            result = self.create(display_name, relative_path)
            if result:
                imported_count += 1
            else:
                errors.append(f'客户 "{display_name}" 已存在或导入失败')
        
        return {
            'success': True,
            'imported_count': imported_count,
            'errors': errors
        }