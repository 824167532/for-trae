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
    
    def _normalize_path(self, *paths):
        """规范化路径，自动处理不同系统的路径分隔符"""
        # 将所有路径部分连接，自动处理分隔符
        joined_path = os.path.join(*paths)
        # 规范化路径（处理反斜杠和正斜杠）
        normalized = os.path.normpath(joined_path)
        return normalized
    
    def save_screenshot(self, customer_path, business_month, filename, image_data):
        """保存截图"""
        # 构建保存路径，自动处理路径分隔符
        save_dir = self._normalize_path(
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
        return self._normalize_path(
            self.root_directory,
            customer_path,
            business_month
        )
    
    def get_invoices_folder(self, customer_path, business_month):
        """获取发票文件夹路径"""
        return self._normalize_path(
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
        """打开文件夹（跨平台支持）"""
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)
        
        system = platform.system()
        
        if system == 'Windows':
            subprocess.run(['explorer', folder_path], shell=True)
        elif system == 'Darwin':  # macOS
            subprocess.run(['open', folder_path])
        elif system == 'Linux':
            subprocess.run(['xdg-open', folder_path])
        else:
            # 默认尝试使用系统打开命令
            subprocess.run(['xdg-open', folder_path], stderr=subprocess.DEVNULL)
        
        return True
    
    def open_folder_and_select_files(self, folder_path):
        """打开文件夹并选中文件（跨平台支持）"""
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)
            # 如果文件夹不存在，直接打开空文件夹
            return self.open_folder(folder_path)
        
        files = os.listdir(folder_path)
        if not files:
            return self.open_folder(folder_path)
        
        system = platform.system()
        
        if system == 'Windows':
            # Windows下选中第一个文件
            first_file = os.path.join(folder_path, files[0])
            subprocess.run(['explorer', '/select,', first_file], shell=True)
        elif system == 'Darwin':
            # macOS下选中所有文件（使用Finder）
            subprocess.run(['open', '-R', folder_path])
        elif system == 'Linux':
            # Linux下直接打开文件夹
            subprocess.run(['xdg-open', folder_path])
        else:
            # 默认处理
            subprocess.run(['xdg-open', folder_path], stderr=subprocess.DEVNULL)
        
        return True
    
    def delete_screenshot(self, customer_path, business_month, filename):
        """删除截图文件"""
        file_path = self._normalize_path(
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
