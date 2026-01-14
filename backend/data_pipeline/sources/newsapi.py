"""NewsAPI 数据源实现"""
import os
import logging
from typing import List
from datetime import datetime
from dateutil import parser

from .base import DataSourceBase, ArticleMetadata

logger = logging.getLogger(__name__)


class NewsAPISource(DataSourceBase):
    """NewsAPI 数据源"""

    # 支持的分类
    CATEGORIES = ["technology", "business", "science", "health", "sports", "entertainment"]

    # 黑名单域名（付费墙或难以爬取）
    BLOCKED_DOMAINS = [
        "wsj.com", "bloomberg.com", "ft.com", "barrons.com",
        "nytimes.com", "washingtonpost.com", "economist.com"
    ]

    # 忽略的标题关键词
    IGNORED_TITLE_KEYWORDS = [
        "patch notes", "changelog", "hotfix", "deal alert",
        "giveaway", "daily wordle", "live blog", "[removed]"
    ]

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("NEWS_API_KEY")
        if not self.api_key:
            raise ValueError("NEWS_API_KEY not set")
        
        # 延迟导入
        from newsapi import NewsApiClient
        self.client = NewsApiClient(api_key=self.api_key)

    @property
    def source_type(self) -> str:
        return "newsapi"

    def get_supported_categories(self) -> List[str]:
        return self.CATEGORIES

    def fetch_articles(self, category: str, count: int) -> List[ArticleMetadata]:
        """获取新闻文章（带过滤）"""
        if category not in self.CATEGORIES:
            logger.warning(f"Unsupported category: {category}")
            return []

        articles = []
        page = 1
        request_page_size = min(100, max(20, count * 2))

        while len(articles) < count:
            try:
                response = self.client.get_top_headlines(
                    category=category,
                    language='en',
                    page_size=request_page_size,
                    page=page
                )

                if response['status'] != 'ok' or not response.get('articles'):
                    break

                for item in response['articles']:
                    if len(articles) >= count:
                        break

                    url = item.get("url")
                    title = item.get("title", "")

                    # 过滤逻辑
                    if not url or not title:
                        continue
                    if any(domain in url for domain in self.BLOCKED_DOMAINS):
                        continue
                    if any(kw in title.lower() for kw in self.IGNORED_TITLE_KEYWORDS):
                        continue

                    # 解析发布时间
                    pub_date = None
                    if item.get("publishedAt"):
                        try:
                            pub_date = parser.parse(item["publishedAt"])
                        except Exception:
                            pass

                    articles.append(ArticleMetadata(
                        title=title,
                        url=url,
                        source='newsapi',
                        source_name=item.get("source", {}).get("name", "Unknown"),
                        category=category,
                        published_at=pub_date,
                        summary=item.get("description", "")[:200] if item.get("description") else None
                    ))

                page += 1
                
                # 防止无限循环
                if page > 5:
                    break

            except Exception as e:
                logger.error(f"NewsAPI error: {e}")
                break

        logger.info(f"Fetched {len(articles)} articles from NewsAPI/{category}")
        return articles
