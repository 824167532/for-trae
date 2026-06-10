"""
文件服务
"""
import os
import re
import base64
import zipfile
import subprocess
import platform
from datetime import datetime


class FileService:
    """文件服务类"""

    def __init__(self, root_directory):
        self.root_directory = root_directory

    def _normalize_path(self, *paths):
        """规范化路径，自动处理不同系统的路径分隔符"""
        joined_path = os.path.join(*paths)
        normalized = os.path.normpath(joined_path)
        return normalized

    # ------------------------------------------------------------------ #
    #  新增: 月份文件夹智能识别（v1.1.3）
    #  支持命名: 202606, 202603-202606, 202606月
    # ------------------------------------------------------------------ #
    def find_month_folder(self, customer_path, business_month):
        """
        智能查找客户目录下匹配业务月份的文件夹

        输入:
            customer_path: 客户相对路径，如 "运营商/移动/广东"
            business_month: 业务月份，格式 YYYY-MM，如 "2026-06"

        返回:
            匹配到的月份文件夹绝对路径，如 /data/客户/202603-202606
            没有匹配返回 None

        支持的文件夹命名:
            202606              -> 匹配 2026-06
            202603-202606       -> 匹配 2026-03/04/05/06
            202606月            -> 匹配 2026-06
        """
        customer_dir = self._normalize_path(self.root_directory, customer_path)
        if not os.path.isdir(customer_dir):
            return None

        # 目标月份: "2026-06" -> "202606"
        target_ym = business_month.replace('-', '')  # "202606"
        target_year = int(target_ym[:4])
        target_month = int(target_ym[4:])

        # 扫描客户目录下的一级子文件夹
        for entry in os.listdir(customer_dir):
            entry_path = os.path.join(customer_dir, entry)
            if not os.path.isdir(entry_path):
                continue

            folder_name = entry

            # 规则1: 直接包含目标年月 "202606"
            # 例如 "202606", "202606月", "202603-202606"（包含 "202606"）
            if target_ym in folder_name:
                return entry_path

            # 规则2: 解析日期范围 "202603-202606"
            # 判断目标月份是否落在范围内（含端点）
            range_match = re.search(r'(\d{6})\s*[-到至]\s*(\d{6})', folder_name)
            if range_match:
                start_ym = range_match.group(1)  # "202603"
                end_ym = range_match.group(2)    # "202606"
                try:
                    start_year = int(start_ym[:4])
                    start_month = int(start_ym[4:])
                    end_year = int(end_ym[:4])
                    end_month = int(end_ym[4:])

                    # 将 yyyymm 转为比较值: year*12 + month
                    target_val = target_year * 12 + target_month
                    start_val = start_year * 12 + start_month
                    end_val = end_year * 12 + end_month

                    if start_val <= target_val <= end_val:
                        return entry_path
                except (ValueError, TypeError):
                    continue

            # 规则3: 提取文件夹名中所有 6 位连续数字段，看是否等于目标
            # 例如 "2026年06月" -> 可能提取不到（因为不连续6位），
            # 但这种格式也会被规则1命中（含 "2026" 和 "06" 但不一定连续），
            # 所以这里做兜底，扫描 "202606月" 等格式
            ym_segments = re.findall(r'\d{6}', folder_name)
            if target_ym in ym_segments:
                return entry_path

        return None

    # ------------------------------------------------------------------ #
    #  新增: 发票文件判断（v1.1.3）
    #  xml -> 直接是发票
    #  pdf/ofd -> 需文件名含20位数字 或 含"发票"/"invoice"
    #  zip -> 需读取内部文件列表判断
    # ------------------------------------------------------------------ #
    def _is_invoice_file(self, filename):
        """
        判断单个文件是否是发票

        规则:
            - .xml  -> True（用户明确说 xml 一定是发票）
            - .pdf/.ofd -> 文件名含 20 位连续数字 或 含"发票"/"invoice" -> True
            - 其他 -> False
        """
        name_lower = filename.lower()
        ext = os.path.splitext(name_lower)[1]

        if ext == '.xml':
            return True

        if ext in ('.pdf', '.ofd'):
            has_invoice_no = bool(re.search(r'\d{20}', filename))
            has_keyword = '发票' in filename or 'invoice' in name_lower
            return has_invoice_no or has_keyword

        return False

    def _scan_zip_for_invoice(self, zip_path):
        """
        读取 zip 内部文件列表，判断 zip 是否含发票

        不实际解压到磁盘，仅读 zip 内部文件名列表
        内部文件规则:
            - .xml -> 发票
            - .pdf/.ofd -> 文件名含 20 位数字 或 含"发票"/"invoice" -> 发票
        返回: True/False
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                for inner_name in zf.namelist():
                    # zipfile 在不同平台对中文文件名编码有差异，做兜底
                    try:
                        display_name = inner_name.encode('cp437').decode('gbk')
                    except (UnicodeEncodeError, UnicodeDecodeError):
                        display_name = inner_name

                    # 用原始名和中文兜底名都判断一次，避免漏判
                    if self._is_invoice_file(inner_name):
                        return True
                    if display_name != inner_name and self._is_invoice_file(display_name):
                        return True

            return False
        except (zipfile.BadZipFile, PermissionError, OSError):
            return False

    def detect_invoice_files(self, customer_path, business_month):
        """
        检测客户某月目录下是否存在发票文件

        步骤:
            1. find_month_folder() 智能识别月目录
            2. 递归扫描月目录下的所有文件
            3. 对每个文件按类型判断:
               - .xml -> 直接发票
               - .pdf/.ofd -> 文件名规则判断
               - .zip -> 读取内部文件列表判断
            4. 收集所有命中的发票文件

        返回: dict
            {
                "has_invoice": True/False,
                "files": ["file1.pdf", "file2.zip"],
                "file_count": 2,
                "folder_path": "/absolute/path/to/月文件夹" 或 None
            }
        """
        month_folder = self.find_month_folder(customer_path, business_month)
        if month_folder is None or not os.path.isdir(month_folder):
            return {
                "has_invoice": False,
                "files": [],
                "file_count": 0,
                "folder_path": None
            }

        invoice_files = []

        for dirpath, _, filenames in os.walk(month_folder):
            for fname in filenames:
                full_path = os.path.join(dirpath, fname)
                ext = os.path.splitext(fname)[1].lower()

                if self._is_invoice_file(fname):
                    invoice_files.append(fname)
                    continue

                if ext == '.zip':
                    if self._scan_zip_for_invoice(full_path):
                        invoice_files.append(fname)

        # 去重（同一个文件名可能出现在不同子目录）
        unique_files = list(dict.fromkeys(invoice_files))

        return {
            "has_invoice": len(unique_files) > 0,
            "files": unique_files,
            "file_count": len(unique_files),
            "folder_path": month_folder
        }

    # ------------------------------------------------------------------ #
    #  保留: 原有的基础函数
    # ------------------------------------------------------------------ #
    def save_screenshot(self, customer_path, business_month, filename, image_data):
        """保存截图"""
        save_dir = self._normalize_path(
            self.root_directory,
            customer_path,
            business_month,
            'screenshots'
        )

        os.makedirs(save_dir, exist_ok=True)

        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]

        file_path = os.path.join(save_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(base64.b64decode(image_data))

        return file_path

    def get_month_folder(self, customer_path, business_month):
        """获取月份文件夹路径（优先使用智能识别的 find_month_folder）"""
        smart_folder = self.find_month_folder(customer_path, business_month)
        if smart_folder is not None:
            return smart_folder
        return self._normalize_path(
            self.root_directory,
            customer_path,
            business_month
        )

    def get_invoices_folder(self, customer_path, business_month):
        """获取发票文件夹路径（与智能月目录保持一致）"""
        month_folder = self.find_month_folder(customer_path, business_month)
        if month_folder is not None:
            return os.path.join(month_folder, 'invoices')
        return self._normalize_path(
            self.root_directory,
            customer_path,
            business_month,
            'invoices'
        )

    def check_invoices_exist(self, customer_path, business_month):
        """
        检查发票是否存在（兼容旧接口，内部调用新的检测逻辑）
        保留此函数是为了向后兼容，新代码应使用 detect_invoice_files()
        """
        result = self.detect_invoice_files(customer_path, business_month)
        return result["has_invoice"]

    def open_folder(self, folder_path):
        """打开文件夹（跨平台支持）"""
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)

        system = platform.system()

        if system == 'Windows':
            subprocess.run(['explorer', folder_path], shell=True)
        elif system == 'Darwin':
            subprocess.run(['open', folder_path])
        elif system == 'Linux':
            subprocess.run(['xdg-open', folder_path])
        else:
            subprocess.run(['xdg-open', folder_path], stderr=subprocess.DEVNULL)

        return True

    def open_folder_and_select_files(self, folder_path):
        """打开文件夹并选中文件（跨平台支持）"""
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)
            return self.open_folder(folder_path)

        files = os.listdir(folder_path)
        if not files:
            return self.open_folder(folder_path)

        system = platform.system()

        if system == 'Windows':
            first_file = os.path.join(folder_path, files[0])
            subprocess.run(['explorer', '/select,', first_file], shell=True)
        elif system == 'Darwin':
            subprocess.run(['open', '-R', folder_path])
        elif system == 'Linux':
            subprocess.run(['xdg-open', folder_path])
        else:
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
        abs_root = os.path.abspath(self.root_directory)
        abs_path = os.path.abspath(path)
        return abs_path.startswith(abs_root)
