"""
文件操作路由
"""
from flask import Blueprint, request, jsonify
from services.settings_service import SettingsService
from services.file_service import FileService

files_bp = Blueprint('files', __name__, url_prefix='/api')
settings_service = SettingsService()


def get_file_service():
    """获取文件服务"""
    root_dir = settings_service.get_root_directory()
    return FileService(root_dir)


@files_bp.route('/open-folder', methods=['POST'])
def open_folder():
    """打开文件夹"""
    data = request.get_json()
    customer_path = data.get('customer_path')
    business_month = data.get('business_month')
    folder_type = data.get('folder_type', 'month')  # month 或 invoices
    
    if not customer_path or not business_month:
        return jsonify({'error': '缺少必要参数'}), 400
    
    file_service = get_file_service()
    
    if folder_type == 'invoices':
        folder_path = file_service.get_invoices_folder(customer_path, business_month)
        file_service.open_folder_and_select_files(folder_path)
    else:
        folder_path = file_service.get_month_folder(customer_path, business_month)
        file_service.open_folder(folder_path)
    
    return jsonify({'success': True})