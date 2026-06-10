"""
待办服务
"""
import sqlite3
from datetime import datetime, timedelta
from models import get_db_connection
from services.file_service import FileService
from services.settings_service import SettingsService


class TodoService:
    """待办服务类"""
    
    def __init__(self):
        self.settings_service = SettingsService()
    
    def get_file_service(self):
        """获取文件服务"""
        root_dir = self.settings_service.get_root_directory()
        return FileService(root_dir)
    
    def get_all(self, send_status='unsent', customer_id=None, business_month=None):
        """获取待办列表"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT t.*, c.display_name as customer_name, c.relative_path as customer_path
            FROM todos t
            JOIN customers c ON t.customer_id = c.id
            WHERE 1=1
        '''
        params = []
        
        if send_status and send_status != 'all':
            query += ' AND t.send_status = ?'
            params.append(send_status)
        
        if customer_id:
            query += ' AND t.customer_id = ?'
            params.append(customer_id)
        
        if business_month:
            query += ' AND t.business_month = ?'
            params.append(business_month)
        
        query += ' ORDER BY t.created_at DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        todos = [dict(row) for row in rows]
        
        # 检查超时状态
        now = datetime.now()
        for todo in todos:
            created_at = datetime.fromisoformat(todo['created_at'])
            if todo['invoice_status'] == 'pending' and (now - created_at) > timedelta(hours=48):
                todo['is_overdue'] = True
            else:
                todo['is_overdue'] = False
        
        return todos
    
    def get_history(self, customer_id=None, business_month=None, send_status=None):
        """获取历史记录（已开票的待办）"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT t.*, c.display_name as customer_name, c.relative_path as customer_path
            FROM todos t
            JOIN customers c ON t.customer_id = c.id
            WHERE t.invoice_status = 'done'
        '''
        params = []
        
        if customer_id:
            query += ' AND t.customer_id = ?'
            params.append(customer_id)
        
        if business_month:
            query += ' AND t.business_month = ?'
            params.append(business_month)
        
        if send_status and send_status != 'all':
            query += ' AND t.send_status = ?'
            params.append(send_status)
        
        query += ' ORDER BY t.completed_at DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        records = [dict(row) for row in rows]

        # 对每条记录查找实际的月份文件夹名
        file_service = self.get_file_service()
        for rec in records:
            folder_name = file_service.get_folder_name(
                rec['customer_path'],
                rec['business_month']
            )
            rec['folder_name'] = folder_name

        return records
    
    def get_by_id(self, todo_id):
        """根据ID获取待办"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT t.*, c.display_name as customer_name, c.relative_path as customer_path
            FROM todos t
            JOIN customers c ON t.customer_id = c.id
            WHERE t.id = ?
            ''',
            (todo_id,)
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def check_duplicate(self, customer_id, business_month):
        """检查是否存在重复待办"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT COUNT(*) as count FROM todos 
            WHERE customer_id = ? AND business_month = ?
            ''',
            (customer_id, business_month)
        )
        result = cursor.fetchone()
        conn.close()
        return result['count'] > 0
    
    def create(self, customer_id, business_month, amount, filename, image_data):
        """创建待办"""
        # 获取客户信息
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT relative_path FROM customers WHERE id = ?', (customer_id,))
        customer = cursor.fetchone()
        if not customer:
            conn.close()
            return None
        
        customer_path = customer['relative_path']
        
        # 保存截图
        file_service = self.get_file_service()
        file_service.save_screenshot(customer_path, business_month, filename, image_data)
        
        # 创建待办记录
        cursor.execute(
            '''
            INSERT INTO todos (customer_id, business_month, amount, screenshot_filename)
            VALUES (?, ?, ?, ?)
            ''',
            (customer_id, business_month, amount, filename)
        )
        conn.commit()
        todo_id = cursor.lastrowid
        conn.close()
        
        return self.get_by_id(todo_id)
    
    def update(self, todo_id, business_month=None, amount=None):
        """更新待办（仅修改记录，不移动文件）"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if business_month:
            updates.append('business_month = ?')
            params.append(business_month)
        
        if amount is not None:
            updates.append('amount = ?')
            params.append(amount)
        
        if updates:
            updates.append('updated_at = ?')
            params.append(datetime.now().isoformat())
            params.append(todo_id)
            
            query = f'UPDATE todos SET {", ".join(updates)} WHERE id = ?'
            cursor.execute(query, params)
            conn.commit()
        
        conn.close()
        return self.get_by_id(todo_id)
    
    def delete(self, todo_id, delete_file=False):
        """删除待办"""
        todo = self.get_by_id(todo_id)
        if not todo:
            return False
        
        # 删除文件
        if delete_file:
            file_service = self.get_file_service()
            file_service.delete_screenshot(
                todo['customer_path'],
                todo['business_month'],
                todo['screenshot_filename']
            )
        
        # 删除记录
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
        conn.commit()
        conn.close()
        
        return True
    
    def refresh_invoice_status(self):
        """刷新开票状态"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取所有待开票的待办
        cursor.execute(
            '''
            SELECT t.id, c.relative_path as customer_path, t.business_month
            FROM todos t
            JOIN customers c ON t.customer_id = c.id
            WHERE t.invoice_status = 'pending'
            '''
        )
        pending_todos = cursor.fetchall()
        
        file_service = self.get_file_service()
        updated_count = 0
        
        for todo in pending_todos:
            result = file_service.detect_invoice_files(
                todo['customer_path'],
                todo['business_month']
            )
            
            if result["has_invoice"]:
                cursor.execute(
                    '''
                    UPDATE todos 
                    SET invoice_status = 'done', completed_at = ?, updated_at = ?
                    WHERE id = ?
                    ''',
                    (datetime.now().isoformat(), datetime.now().isoformat(), todo['id'])
                )
                updated_count += 1
        
        conn.commit()
        conn.close()
        
        return updated_count
    
    def mark_sent(self, todo_id):
        """标记已发送"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查状态
        cursor.execute(
            'SELECT invoice_status, send_status FROM todos WHERE id = ?',
            (todo_id,)
        )
        todo = cursor.fetchone()
        
        if not todo or todo['invoice_status'] != 'done' or todo['send_status'] != 'unsent':
            conn.close()
            return False
        
        # 更新状态
        cursor.execute(
            '''
            UPDATE todos 
            SET send_status = 'sent', sent_at = ?, updated_at = ?
            WHERE id = ?
            ''',
            (datetime.now().isoformat(), datetime.now().isoformat(), todo_id)
        )
        conn.commit()
        conn.close()
        
        return True
    
    def get_missing_current_month(self):
        """获取当月没有开票完成的客户（有未完成待办/完全没有待办都算遗漏）"""
        current_month = datetime.now().strftime('%Y-%m')

        conn = get_db_connection()
        cursor = conn.cursor()

        # 获取所有客户
        cursor.execute('SELECT id, display_name FROM customers')
        all_customers = cursor.fetchall()

        # 获取当月 invoice_status='done'（已完成开票）的客户
        cursor.execute(
            '''
            SELECT DISTINCT customer_id FROM todos
            WHERE business_month = ? AND invoice_status = 'done'
            ''',
            (current_month,)
        )
        customers_done = [row['customer_id'] for row in cursor.fetchall()]

        conn.close()

        # 没有完成开票的客户算遗漏（有 pending 待办但没完成 / 完全没有待办）
        missing_customers = [
            {'id': row['id'], 'display_name': row['display_name']}
            for row in all_customers
            if row['id'] not in customers_done
        ]

        return missing_customers