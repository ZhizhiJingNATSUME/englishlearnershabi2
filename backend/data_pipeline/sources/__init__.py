"""数据源工厂"""
from typing import List

from .base import DataSourceBase, ArticleMetadata
from .newsapi import NewsAPISource
from .voa import VOASource
from .wikipedia import WikipediaSource


class DataSourceFactory:
    """数据源工厂类"""

    _sources = {
        'newsapi': NewsAPISource,
        'voa': VOASource,
        'wikipedia': WikipediaSource
    }

    @classmethod
    def create(cls, source_type: str) -> DataSourceBase:
        """
        创建数据源实例

        Args:
            source_type: 'newsapi', 'voa', 'wikipedia'
        """
        if source_type not in cls._sources:
            raise ValueError(f"Unknown source type: {source_type}. Available: {list(cls._sources.keys())}")

        return cls._sources[source_type]()

    @classmethod
    def get_available_sources(cls) -> List[str]:
        """获取所有可用数据源"""
        return list(cls._sources.keys())


__all__ = [
    'DataSourceBase',
    'ArticleMetadata',
    'NewsAPISource',
    'VOASource',
    'WikipediaSource',
    'DataSourceFactory'
]
