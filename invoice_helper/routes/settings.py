"""
设置路由
"""
from flask import Blueprint, request, jsonify
from services.settings_service import SettingsService

settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')
settings_service = SettingsService()


@settings_bp.route('', methods=['GET'])
def get_settings():
    """获取所有设置"""
    settings = settings_service.get_all()
    return jsonify(settings)


@settings_bp.route('', methods=['POST'])
def save_settings():
    """保存设置"""
    data = request.get_json()
    root_directory = data.get('root_directory')
    
    if root_directory:
        settings_service.set_root_directory(root_directory)
    
    return jsonify({'success': True})


@settings_bp.route('/root-directory', methods=['GET'])
def get_root_directory():
    """获取根目录"""
    root_dir = settings_service.get_root_directory()
    return jsonify({'root_directory': root_dir})