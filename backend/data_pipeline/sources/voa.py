"""VOA Learning English 数据源"""
import logging
from typing import List
from datetime import datetime

import feedparser

from .base import DataSourceBase, ArticleMetadata

logger = logging.getLogger(__name__)


class VOASource(DataSourceBase):
    """VOA Learning English 数据源"""

    # VOA Learning English RSS 源 (mapped to 8 standardized categories)
    RSS_FEEDS = {
        "science": "https://learningenglish.voanews.com/api/zmg_pl-vomx-tpeymtm",  # Science & Technology
        "health": "https://learningenglish.voanews.com/api/zmmpql-vomx-tpey-_q",   # Health & Lifestyle
        "education": "https://learningenglish.voanews.com/api/ztmp_l-vomx-tpek-__",  # Education + Grammar + Words
        "culture": "https://learningenglish.voanews.com/api/zpyp_l-vomx-tpe_rym",   # Arts & Culture
        "grammar": "https://learningenglish.voanews.com/api/zoroqql-vomx-tpeptpqq",  # Everyday Grammar
        "stories": "https://learningenglish.voanews.com/api/zyg__l-vomx-tpetmty",   # American Stories
        "words": "https://learningenglish.voanews.com/api/zmypyl-vomx-tpeyry_",     # Words and Their Stories
        "news": "https://learningenglish.voanews.com/api/zkm-ql-vomx-tpej-rqi"      # As It Is (News)
    }

    @property
    def source_type(self) -> str:
        return "voa"

    def get_supported_categories(self) -> List[str]:
        return list(self.RSS_FEEDS.keys())

    def fetch_articles(self, category: str, count: int) -> List[ArticleMetadata]:
        """从 RSS Feed 获取 VOA 文章"""
        if category not in self.RSS_FEEDS:
            logger.warning(f"Unsupported VOA category: {category}")
            return []

        feed_url = self.RSS_FEEDS[category]
        articles = []

        try:
            feed = feedparser.parse(feed_url)

            if feed.bozo:
                logger.warning(f"RSS parsing warning: {feed.bozo_exception}")

            for entry in feed.entries[:count]:
                try:
                    # 解析发布时间
                    pub_date = None
                    if hasattr(entry, 'published'):
                        try:
                            from email.utils import parsedate_to_datetime
                            pub_date = parsedate_to_datetime(entry.published)
                        except Exception:
                            pass

                    # 提取摘要
                    summary = entry.get('summary', '')
                    if summary:
                        # 移除 HTML 标签
                        import re
                        summary = re.sub(r'<[^>]+>', '', summary)[:200]

                    articles.append(ArticleMetadata(
                        title=entry.get('title', 'Untitled'),
                        url=entry.get('link', ''),
                        source='voa',
                        source_name='VOA Learning English',
                        category=category,
                        published_at=pub_date,
                        summary=summary
                    ))

                except Exception as e:
                    logger.error(f"Error parsing RSS entry: {e}")
                    continue

            logger.info(f"Fetched {len(articles)} VOA articles from {category}")

        except Exception as e:
            logger.error(f"Error fetching VOA RSS: {e}")

        return articles
