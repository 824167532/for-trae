"""
文件夹扫描路由 - 扫描本地目录获取客户候选文件夹
"""
import os
from flask import Blueprint, request, jsonify
from pathlib import Path

scan_bp = Blueprint('scan', __name__, url_prefix='/api/scan')


def _should_skip_directory(name):
    """判断是否应该跳过的目录"""
    skip_prefixes = ['.', '__', '$']
    skip_names = [
        'screenshots', 'invoices', '截图', '发票', '发票文件',
        'temp', 'tmp', 'cache', 'data', 'backup', 'bak',
        'system volume information', '$recycle.bin'
    ]
    
    # 检查前缀
    for prefix in skip_prefixes:
        if name.lower().startswith(prefix.lower()):
            return True
    
    # 检查名称
    if name.lower() in skip_names:
        return True
    
    return False


def _scan_directory_recursive(base_path, max_depth=3, current_depth=0):
    """递归扫描目录，返回文件夹列表（包含嵌套结构）"""
    folders = []
    
    try:
        base_path = Path(base_path)
        if not base_path.exists() or not base_path.is_dir():
            return folders
        
        # 获取直接子目录
        for item in base_path.iterdir():
            if item.is_dir():
                name = item.name
                
                # 跳过不需要的目录
                if _should_skip_directory(name):
                    continue
                
                # 计算相对路径
                rel_path = str(item.relative_to(base_path.parent))
                
                # 检查是否还有子目录（不包含 screenshots/invoices 的子目录）
                has_sub_dirs = False
                try:
                    for sub in item.iterdir():
                        if sub.is_dir() and not _should_skip_directory(sub.name):
                            has_sub_dirs = True
                            break
                except (PermissionError, OSError):
                    pass
                
                folder_info = {
                    'display_name': name,
                    'relative_path': rel_path,
                    'full_path': str(item),
                    'has_sub_dirs': has_sub_dirs,
                    'depth': current_depth
                }
                folders.append(folder_info)
                
                # 如果有子目录且未达到最大深度，继续扫描子目录
                if has_sub_dirs and current_depth < max_depth - 1:
                    sub_folders = _scan_directory_recursive(item, max_depth, current_depth + 1)
                    # 对子目录路径进行修正（加上当前目录）
                    for sf in sub_folders:
                        # 重新计算相对路径（相对于原始 base_path 的父目录）
                        sf_rel = str(Path(sf['full_path']).relative_to(base_path.parent))
                        sf['relative_path'] = sf_rel
                    folders.extend(sub_folders)
                    
    except (PermissionError, OSError):
        pass
    
    return folders


@scan_bp.route('/folders', methods=['POST'])
def scan_folders():
    """扫描指定目录下的文件夹"""
    data = request.get_json()
    base_dir = data.get('base_dir')
    
    if not base_dir:
        return jsonify({'error': '请输入目录路径'}), 400
    
    # 规范化路径
    base_dir = os.path.normpath(os.path.expanduser(base_dir))
    
    # 检查目录是否存在
    if not os.path.exists(base_dir):
        return jsonify({'error': f'目录不存在: {base_dir}'}), 400
    
    if not os.path.isdir(base_dir):
        return jsonify({'error': '该路径不是一个目录'}), 400
    
    # 获取最大深度参数
    max_depth = data.get('max_depth', 3)
    try:
        max_depth = int(max_depth)
    except (ValueError, TypeError):
        max_depth = 3
    
    # 限制最大深度范围
    max_depth = max(1, min(max_depth, 5))
    
    try:
        # 扫描子目录
        folders = []
        
        base_path = Path(base_dir)
        for item in base_path.iterdir():
            if item.is_dir():
                name = item.name
                
                # 跳过不需要的目录
                if _should_skip_directory(name):
                    continue
                
                # 检查是否有子目录
                has_sub_dirs = False
                try:
                    for sub in item.iterdir():
                        if sub.is_dir() and not _should_skip_directory(sub.name):
                            has_sub_dirs = True
                            break
                except (PermissionError, OSError):
                    pass
                
                folder_info = {
                    'display_name': name,
                    'relative_path': name,
                    'full_path': str(item),
                    'has_sub_dirs': has_sub_dirs
                }
                folders.append(folder_info)
                
                # 扫描嵌套目录（如果需要）
                if has_sub_dirs and max_depth > 1:
                    try:
                        for sub_item in item.iterdir():
                            if sub_item.is_dir() and not _should_skip_directory(sub_item.name):
                                sub_name = sub_item.name
                                sub_rel = f"{name}\\{sub_name}"
                                folders.append({
                                    'display_name': sub_name,
                                    'relative_path': sub_rel,
                                    'full_path': str(sub_item),
                                    'has_sub_dirs': False
                                })
                    except (PermissionError, OSError):
                        pass
        
        # 按名称排序
        folders.sort(key=lambda x: x['display_name'])
        
        return jsonify({
            'success': True,
            'base_dir': base_dir,
            'total': len(folders),
            'folders': folders
        })
        
    except Exception as e:
        return jsonify({'error': f'扫描失败: {str(e)}'}), 500


@scan_bp.route('/validate', methods=['POST'])
def validate_path():
    """验证路径是否存在"""
    data = request.get_json()
    path = data.get('path')
    
    if not path:
        return jsonify({'valid': False, 'error': '路径不能为空'}), 400
    
    path = os.path.normpath(os.path.expanduser(path))
    
    if os.path.exists(path):
        if os.path.isdir(path):
            return jsonify({'valid': True, 'is_dir': True, 'path': path})
        else:
            return jsonify({'valid': True, 'is_dir': False, 'path': path})
    else:
        return jsonify({'valid': False, 'is_dir': False, 'path': path})
