"""数据源抽象基类"""
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ArticleMetadata:
    """统一的文章元数据"""
    title: str
    url: str
    source: str  # 'newsapi', 'voa', 'wikipedia'
    source_name: str  # 具体来源
    category: str
    published_at: Optional[datetime] = None
    summary: Optional[str] = None  # 预览摘要
    audio_url: Optional[str] = None  # VOA 音频


class DataSourceBase(ABC):
    """数据源基类"""

    @abstractmethod
    def fetch_articles(self, category: str, count: int) -> List[ArticleMetadata]:
        """
        获取文章元数据列表

        Args:
            category: 类别
            count: 数量

        Returns:
            ArticleMetadata 列表
        """
        pass

    @abstractmethod
    def get_supported_categories(self) -> List[str]:
        """返回支持的类别列表"""
        pass

    @property
    @abstractmethod
    def source_type(self) -> str:
        """数据源类型标识"""
        pass
