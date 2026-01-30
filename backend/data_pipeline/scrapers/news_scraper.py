"""
新闻爬虫 - 输出纯文本
使用 newspaper4k (newspaper3k 的现代化分支)
"""
import asyncio
import logging
import re
from typing import Optional

from newspaper import Article, Config

logger = logging.getLogger(__name__)


class NewsScraper:
    """新闻爬虫（纯文本输出）- 使用 newspaper4k"""

    def __init__(self):
        self.config = Config()
        self.config.browser_user_agent = (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        )
        self.config.request_timeout = 15
        self.config.fetch_images = False
        self.config.memoize_articles = False
        # newspaper4k 特性: 可选 cloudscraper 绕过 Cloudflare
        # self.config.use_cloudscraper = True  # 需要安装 cloudscraper

    async def scrape_article(self, url: str) -> Optional[str]:
        """
        爬取文章内容（纯文本）

        Args:
            url: 文章 URL

        Returns:
            纯文本内容或 None
        """
        logger.info(f"Scraping: {url}")

        loop = asyncio.get_running_loop()

        def _sync_scrape():
            try:
                article = Article(url, config=self.config)
                article.download()
                article.parse()

                # 获取纯文本
                content = article.text

                if not content:
                    logger.warning(f"No content extracted from {url}")
                    return None

                # 清洗文本
                content = self._clean_text(content)

                # 检查长度
                if len(content) < 300:
                    logger.warning(f"Content too short: {len(content)} chars")
                    return None

                # 组合标题和内容
                title = article.title or ""
                if title and not content.startswith(title):
                    full_text = f"{title}\n\n{content}"
                else:
                    full_text = content

                return full_text

            except Exception as e:
                logger.error(f"Scraping error for {url}: {e}")
                return None

        return await loop.run_in_executor(None, _sync_scrape)

    def _clean_text(self, text: str) -> str:
        """清洗文本"""
        if not text:
            return ""

        # 移除常见垃圾文本
        patterns_to_remove = [
            r'(?i)toggle caption\s*',
            r'(?i)click to expand\s*',
            r'(?i)advertisement\s*',
            r'(?i)sponsored content\s*',
            r'(?i)read more:.*',
            r'(?i)subscribe to.*',
            r'(?i)sign up for.*',
        ]
        
        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text)

        # 标准化换行
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # 折叠多余空白
        text = re.sub(r'[^\S\n]+', ' ', text)

        # 标准化段落
        text = re.sub(r'\n\s*\n', '\n\n', text)

        # 移除行首行尾空白
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)

        return text.strip()
