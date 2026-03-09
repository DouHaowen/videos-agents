"""
知识库模块
提供数据库存储和管理功能
"""

from .database import MeetingDatabase
from .search import MeetingSearchEngine

__all__ = ['MeetingDatabase', 'MeetingSearchEngine']
