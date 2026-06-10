"""
发布打包脚本
将项目文件打包成一个完整的发布包
"""
import os
import sys
import shutil
import zipfile
import json
from datetime import datetime
from pathlib import Path

# 添加项目目录到路径，以便导入 version_utils
PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))

from version_utils import get_version, get_version_name


def get_project_files():
    """
    获取需要打包的项目文件列表
    
    返回: (相对路径列表, 目录列表)
    """
    # 核心代码文件
    code_files = [
        'app.py',
        'models.py',
        'version_utils.py',
        'version.json',
        'requirements.txt',
        'README.md',
        'UPGRADE_GUIDE.md',
        'start.bat',      # Windows 启动脚本
        'start.sh',       # macOS/Linux 终端启动脚本
        'start.command',  # macOS 双击启动脚本
    ]
    
    # 需要完整包含的目录（递归）
    directories = [
        'routes',
        'services',
        'templates',
        'static',
    ]
    
    return code_files, directories


def collect_files_for_package(source_dir: Path):
    """
    收集所有要打包的文件
    
    参数:
        source_dir: 项目根目录
        
    返回: 相对路径的列表
    """
    code_files, directories = get_project_files()
    all_files = list(code_files)
    
    # 递归添加目录中的所有文件
    for directory in directories:
        dir_path = source_dir / directory
        if dir_path.exists():
            for file_path in dir_path.rglob('*'):
                if file_path.is_file():
                    # 只添加源码文件，跳过 __pycache__ 等
                    rel_path = file_path.relative_to(source_dir)
                    # 排除不需要的文件
                    if '__pycache__' in str(rel_path):
                        continue
                    if file_path.suffix in ('.pyc',):
                        continue
                    # 添加到列表
                    all_files.append(str(rel_path).replace('\\', '/'))
    
    return sorted(all_files)


def create_package():
    """
    创建发布包
    
    返回: 生成的 zip 文件的路径
    """
    # 获取版本信息
    version = get_version()
    version_name = get_version_name()
    
    # 创建一个临时的发布目录
    package_name = f'invoice_helper_v{version}'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    releases_dir = PROJECT_DIR.parent / 'releases'
    releases_dir.mkdir(exist_ok=True)
    
    # 临时构建目录
    build_dir = PROJECT_DIR.parent / f'build_{package_name}_{timestamp}'
    build_dir.mkdir(parents=True, exist_ok=True)
    package_dir = build_dir / package_name
    package_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print(f"    正在构建发布包: {package_name}")
    print(f"    版本: {version}")
    print(f"    构建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    # 1. 收集要复制的文件
    files_to_copy = collect_files_for_package(PROJECT_DIR)
    print(f"[1/4] 共收集到 {len(files_to_copy)} 个文件需要复制")
    
    # 2. 复制文件到构建目录
    copied_count = 0
    for file_rel_path in files_to_copy:
        source_file = PROJECT_DIR / file_rel_path
        target_file = package_dir / file_rel_path
        
        # 确保目标目录存在
        target_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 复制文件
        if source_file.exists():
            shutil.copy2(source_file, target_file)
            copied_count += 1
            print(f"  ✓ {file_rel_path}")
    
    print(f"\n[2/4] 已复制 {copied_count} 个文件")
    
    # 3. 在构建目录中创建必要的空目录
    data_dir = package_dir / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建一个占位文件（用于保持目录结构，因为空目录不会被打包进 zip）
    (data_dir / '.gitkeep').write_text('此目录用于存放数据库文件\n', encoding='utf-8')
    
    print(f"[3/4] 已创建必要的目录结构")
    
    # 4. 创建 ZIP 文件
    zip_file_path = releases_dir / f'{package_name}.zip'
    
    # 如果已存在同名文件，先删除
    if zip_file_path.exists():
        zip_file_path.unlink()
    
    # 打包
    print(f"\n[4/4] 正在创建压缩包: {zip_file_path.name}")
    
    file_count = 0
    with zipfile.ZipFile(str(zip_file_path), 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        # 遍历构建目录中的所有文件
        for file_path in package_dir.rglob('*'):
            if file_path.is_file():
                # 在 zip 中的路径（相对于 build 目录）
                arcname = file_path.relative_to(build_dir)
                zipf.write(str(file_path), arcname=str(arcname))
                file_count += 1
    
    print(f"  ✓ 已打包 {file_count} 个文件")
    
    # 获取文件大小
    file_size_mb = zip_file_path.stat().st_size / (1024 * 1024)
    
    # 清理临时构建目录
    shutil.rmtree(build_dir)
    
    print()
    print("=" * 60)
    print(f"  🎉 发布包构建完成!")
    print("=" * 60)
    print(f"  文件名: {zip_file_path.name}")
    print(f"  完整路径: {zip_file_path}")
    print(f"  文件大小: {file_size_mb:.2f} MB")
    print(f"  版本: {version}")
    print(f"  版本名称: {version_name}")
    print(f"  打包时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    print(f"  使用方法:")
    print(f"  1. 将 {zip_file_path.name} 解压到任意目录")
    print(f"  2. Windows 用户: 双击 start.bat")
    print(f"  3. macOS 用户: 在终端执行 ./start.sh 或 python3 app.py")
    print()
    
    return zip_file_path


if __name__ == '__main__':
    try:
        create_package()
    except Exception as e:
        print(f"\n❌ 打包失败: {e}")
        sys.exit(1)
