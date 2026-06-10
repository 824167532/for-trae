"""
版本管理模块 - 版本号的唯一真源
所有需要版本号的地方都通过此模块读取，确保一致性
"""
import os
import json
from typing import Dict, Optional


# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
VERSION_FILE = os.path.join(PROJECT_ROOT, 'version.json')


def _load_version_file() -> Dict:
    """
    加载版本配置文件
    
    Returns:
        版本配置字典
    
    Raises:
        FileNotFoundError: version.json不存在
        ValueError: version.json格式错误
    """
    if not os.path.exists(VERSION_FILE):
        raise FileNotFoundError(
            f"版本配置文件不存在: {VERSION_FILE}。请确保项目根目录下有 version.json 文件。"
        )
    
    try:
        with open(VERSION_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"版本配置文件格式错误: {e}")
    
    if 'version' not in config:
        raise ValueError("版本配置文件缺少 'version' 字段")
    
    return config


def get_version() -> str:
    """
    获取当前版本号
    
    Returns:
        版本号字符串，例如 "1.0.0"
    
    Raises:
        FileNotFoundError: version.json不存在
        ValueError: version.json格式错误或缺少version字段
    """
    config = _load_version_file()
    return config['version']


def get_version_info() -> Dict:
    """
    获取完整的版本信息
    
    Returns:
        包含完整版本信息的字典
    
    Raises:
        FileNotFoundError: version.json不存在
        ValueError: version.json格式错误
    """
    return _load_version_file()


def get_version_name() -> str:
    """
    获取版本名称（含标题）
    
    Returns:
        版本名称，例如 "开票待办助手 v1.0.0"
    """
    config = _load_version_file()
    return config.get('version_name', f'开票待办助手 v{config.get("version", "unknown")}')


def get_release_date() -> str:
    """
    获取发布日期
    
    Returns:
        发布日期字符串，例如 "2026-06-10"
    """
    config = _load_version_file()
    return config.get('release_date', '')


def get_version_tuple() -> tuple:
    """
    获取元组格式的版本号，用于比较
    
    Returns:
        版本号元组，例如 (1, 0, 0)
    """
    version = get_version()
    parts = version.split('.')
    result = []
    for part in parts:
        try:
            # 提取数字部分（处理可能的后缀如 1.0.0-beta）
            num_part = ''.join(c for c in part if c.isdigit())
            if num_part:
                result.append(int(num_part))
            else:
                result.append(0)
        except ValueError:
            result.append(0)
    # 确保至少是三元组
    while len(result) < 3:
        result.append(0)
    return tuple(result[:3])


def compare_version(other_version: str) -> int:
    """
    比较版本号
    
    Args:
        other_version: 要比较的版本号字符串
    
    Returns:
        1: 当前版本更新
        0: 版本相同
        -1: 当前版本较旧
    """
    current = get_version_tuple()
    
    # 解析另一个版本号
    parts = other_version.split('.')
    other = []
    for part in parts:
        try:
            num_part = ''.join(c for c in part if c.isdigit())
            if num_part:
                other.append(int(num_part))
            else:
                other.append(0)
        except ValueError:
            other.append(0)
    while len(other) < 3:
        other.append(0)
    other = tuple(other[:3])
    
    if current > other:
        return 1
    elif current < other:
        return -1
    return 0


if __name__ == '__main__':
    # 测试输出版本信息
    print(f"版本号: {get_version()}")
    print(f"完整名称: {get_version_name()}")
    print(f"发布日期: {get_release_date()}")
    print(f"版本元组: {get_version_tuple()}")
    print()
    print("完整配置:")
    print(json.dumps(get_version_info(), ensure_ascii=False, indent=2))
