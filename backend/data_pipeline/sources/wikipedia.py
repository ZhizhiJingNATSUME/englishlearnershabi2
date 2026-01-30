"""Wikipedia 数据源"""
import logging
from typing import List

import wikipedia

from .base import DataSourceBase, ArticleMetadata

logger = logging.getLogger(__name__)


class WikipediaSource(DataSourceBase):
    """Wikipedia 数据源"""

    # 分类 → 搜索关键词映射 (all lowercase for consistency)
    CATEGORY_KEYWORDS = {
        "technology": [
            "artificial intelligence", "machine learning", "computer science",
            "software engineering", "internet", "robotics", "blockchain",
            "virtual reality", "cybersecurity", "smartphone"
        ],
        "science": [
            "physics", "biology", "chemistry", "astronomy",
            "mathematics", "ecology", "genetics", "quantum mechanics",
            "space exploration"
        ],
        "health": [
            "nutrition", "exercise", "mental health",
            "epidemiology", "immune system", "disease prevention",
            "medical science", "psychology"
        ],
        "business": [
            "economics", "stock market", "entrepreneurship",
            "marketing", "international trade", "corporate finance",
            "management", "accounting"
        ],
        "education": [
            "education system", "learning theory", "university",
            "online education", "educational psychology",
            "teaching methods", "school"
        ],
        "culture": [
            "art history", "classical music", "literature",
            "philosophy", "world religions", "cultural traditions",
            "museum", "architecture"
        ],
        "sports": [
            "olympic games", "football", "basketball",
            "tennis", "athletics", "sports science",
            "world cup", "championship"
        ],
        "entertainment": [
            "film history", "television", "video games",
            "popular music", "theater", "celebrity",
            "cinema", "streaming"
        ]
    }

    def __init__(self):
        # 设置 Wikipedia 语言
        wikipedia.set_lang("en")

    @property
    def source_type(self) -> str:
        return "wikipedia"

    def get_supported_categories(self) -> List[str]:
        return list(self.CATEGORY_KEYWORDS.keys())

    def fetch_articles(self, category: str, count: int) -> List[ArticleMetadata]:
        """搜索 Wikipedia 文章"""
        if category not in self.CATEGORY_KEYWORDS:
            logger.warning(f"Unsupported Wikipedia category: {category}")
            return []

        keywords = self.CATEGORY_KEYWORDS[category]
        articles = []
        articles_per_keyword = max(1, count // len(keywords))

        for keyword in keywords:
            if len(articles) >= count:
                break

            try:
                # 搜索相关文章
                search_results = wikipedia.search(keyword, results=articles_per_keyword + 2)

                for title in search_results:
                    if len(articles) >= count:
                        break

                    try:
                        # 获取页面信息
                        page = wikipedia.page(title, auto_suggest=False)

                        # 检查是否已添加（去重）
                        if any(a.url == page.url for a in articles):
                            continue

                        articles.append(ArticleMetadata(
                            title=page.title,
                            url=page.url,
                            source='wikipedia',
                            source_name='Wikipedia',
                            category=category,
                            summary=page.summary[:200] if page.summary else None
                        ))

                    except wikipedia.exceptions.DisambiguationError as e:
                        # 歧义页面，尝试第一个选项
                        if e.options:
                            try:
                                page = wikipedia.page(e.options[0], auto_suggest=False)
                                articles.append(ArticleMetadata(
                                    title=page.title,
                                    url=page.url,
                                    source='wikipedia',
                                    source_name='Wikipedia',
                                    category=category,
                                    summary=page.summary[:200] if page.summary else None
                                ))
                            except Exception:
                                pass
                    except wikipedia.exceptions.PageError:
                        continue
                    except Exception as e:
                        logger.debug(f"Error fetching Wikipedia page '{title}': {e}")
                        continue

            except Exception as e:
                logger.error(f"Wikipedia search error for '{keyword}': {e}")
                continue

        logger.info(f"Fetched {len(articles)} Wikipedia articles from {category}")
        return articles[:count]
