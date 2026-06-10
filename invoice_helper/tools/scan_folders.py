"""
文件夹扫描工具 - 批量获取客户文件夹路径
运行此脚本，扫描指定目录下的所有子文件夹，生成可导入的客户列表
"""
import os
import sys
import json
from pathlib import Path

def scan_folders(base_path):
    """
    扫描指定目录下的所有子文件夹
    
    参数:
        base_path: 要扫描的根目录路径
        
    返回:
        文件夹列表，每个元素包含 (文件夹名, 相对路径)
    """
    folders = []
    base_path = Path(base_path)
    
    if not base_path.exists():
        print(f"[错误] 目录不存在: {base_path}")
        return folders
    
    # 遍历所有子目录
    for item in base_path.rglob('*'):
        if item.is_dir():
            # 获取相对路径
            rel_path = item.relative_to(base_path)
            # 获取文件夹名（最后一层）
            folder_name = item.name
            
            # 排除一些特殊目录
            if folder_name.startswith('.') or folder_name.startswith('__'):
                continue
            if folder_name.lower() in ['screenshots', 'invoices', 'data', 'temp']:
                continue
            
            folders.append((folder_name, str(rel_path)))
    
    return folders


def generate_excel_import_data(folders, root_dir):
    """
    生成Excel导入格式的数据
    
    参数:
        folders: 文件夹列表
        root_dir: 根目录
        
    返回:
        可用于Excel导入的数据列表
    """
    data = []
    for folder_name, rel_path in folders:
        data.append({
            'display_name': folder_name,
            'relative_path': rel_path
        })
    return data


def main():
    print("=" * 60)
    print("    文件夹扫描工具 - 批量获取客户路径")
    print("=" * 60)
    print()
    
    # 获取用户输入的扫描目录
    if len(sys.argv) > 1:
        scan_dir = sys.argv[1]
    else:
        print("请输入要扫描的目录路径（客户文件夹所在的根目录）：")
        print("例如：/Users/xiaomai/Documents/财务资料")
        print("或者：D:\\财务资料")
        print()
        scan_dir = input("目录路径: ").strip()
    
    if not scan_dir:
        print("[错误] 未输入目录路径")
        return
    
    # 规范化路径
    scan_dir = os.path.normpath(scan_dir)
    
    print()
    print(f"[1/3] 正在扫描目录: {scan_dir}")
    print()
    
    # 扫描文件夹
    folders = scan_folders(scan_dir)
    
    if not folders:
        print("[提示] 未找到任何客户文件夹")
        return
    
    print(f"[2/3] 找到 {len(folders)} 个文件夹")
    print()
    print("找到的文件夹列表：")
    print("-" * 60)
    for i, (name, path) in enumerate(folders, 1):
        print(f"  {i:3d}. {name} -> {path}")
    print("-" * 60)
    print()
    
    # 生成输出文件
    output_file = Path(scan_dir) / '客户文件夹列表.json'
    
    # 构建输出数据
    output_data = {
        'root_directory': scan_dir,
        'scan_time': str(Path(scan_dir).stat().st_mtime),
        'total_folders': len(folders),
        'folders': generate_excel_import_data(folders, scan_dir)
    }
    
    # 写入JSON文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"[3/3] 已生成文件: {output_file}")
    print()
    print("=" * 60)
    print("  🎉 扫描完成!")
    print("=" * 60)
    print()
    print("下一步操作：")
    print("  1. 打开开票待办助手，进入「设置」页面")
    print("  2. 将根目录设置为:", scan_dir)
    print("  3. 下载Excel导入模板")
    print("  4. 将扫描结果填入模板的「客户名称」和「相对路径」列")
    print("  5. 导入Excel文件")
    print()
    print(f"扫描结果已保存到: {output_file}")
    print("您可以直接打开这个JSON文件查看完整列表")
    print()


if __name__ == '__main__':
    main()