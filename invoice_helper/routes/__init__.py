"""
路由模块
"""
from .customers import customers_bp
from .todos import todos_bp
from .settings import settings_bp
from .files import files_bp

__all__ = ['customers_bp', 'todos_bp', 'settings_bp', 'files_bp']