"""
文件服务
"""
import os
import base64
import subprocess
import platform
from datetime import datetime


class FileService:
    """文件服务类"""
    
    def __init__(self, root_directory):
        self.root_directory = root_directory
    
    def save_screenshot(self, customer_path, business_month, filename, image_data):
        """保存截图"""
        # 构建保存路径
        save_dir = os.path.join(
            self.root_directory,
            customer_path,
            business_month,
            'screenshots'
        )
        
        # 创建目录
        os.makedirs(save_dir, exist_ok=True)
        
        # 解析base64数据
        if image_data.startswith('data:image'):
            # 移除data:image/png;base64,前缀
            image_data = image_data.split(',')[1]
        
        # 保存文件
        file_path = os.path.join(save_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(base64.b64decode(image_data))
        
        return file_path
    
    def get_month_folder(self, customer_path, business_month):
        """获取月份文件夹路径"""
        return os.path.join(
            self.root_directory,
            customer_path,
            business_month
        )
    
    def get_invoices_folder(self, customer_path, business_month):
        """获取发票文件夹路径"""
        return os.path.join(
            self.root_directory,
            customer_path,
            business_month,
            'invoices'
        )
    
    def check_invoices_exist(self, customer_path, business_month):
        """检查发票是否存在"""
        invoice_dir = self.get_invoices_folder(customer_path, business_month)
        if not os.path.exists(invoice_dir):
            return False
        
        invoice_extensions = {'.pdf', '.xml', '.ofd'}
        files = os.listdir(invoice_dir)
        return any(
            os.path.splitext(f)[1].lower() in invoice_extensions
            for f in files
        )
    
    def open_folder(self, folder_path):
        """打开文件夹"""
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)
        
        if platform.system() == 'Windows':
            subprocess.run(['explorer', folder_path])
        elif platform.system() == 'Darwin':  # macOS
            subprocess.run(['open', folder_path])
        else:  # Linux
            subprocess.run(['xdg-open', folder_path])
        
        return True
    
    def open_folder_and_select_files(self, folder_path):
        """打开文件夹并选中文件"""
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)
            # 如果文件夹不存在，直接打开空文件夹
            return self.open_folder(folder_path)
        
        files = os.listdir(folder_path)
        if not files:
            return self.open_folder(folder_path)
        
        if platform.system() == 'Windows':
            # Windows下选中第一个文件
            first_file = os.path.join(folder_path, files[0])
            subprocess.run(['explorer', '/select,', first_file])
        elif platform.system() == 'Darwin':
            # macOS下选中所有文件
            subprocess.run(['open', '-R', folder_path])
        else:
            subprocess.run(['xdg-open', folder_path])
        
        return True
    
    def delete_screenshot(self, customer_path, business_month, filename):
        """删除截图文件"""
        file_path = os.path.join(
            self.root_directory,
            customer_path,
            business_month,
            'screenshots',
            filename
        )
        
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    
    def validate_path(self, path):
        """验证路径是否在根目录范围内"""
        # 规范化路径
        abs_root = os.path.abspath(self.root_directory)
        abs_path = os.path.abspath(path)
        
        # 检查路径是否在根目录下
        return abs_path.startswith(abs_root)