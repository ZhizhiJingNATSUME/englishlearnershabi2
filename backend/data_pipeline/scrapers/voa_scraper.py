"""VOA 爬虫 - 提取纯文本和音频
使用 newspaper4k (newspaper3k 的现代化分支)
"""
import asyncio
import logging
import re
from typing import Optional, Dict

import requests
from bs4 import BeautifulSoup
from newspaper import Article, Config

logger = logging.getLogger(__name__)


class VOAScraper:
    """VOA Learning English 爬虫"""

    def __init__(self):
        self.config = Config()
        self.config.browser_user_agent = (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        )
        self.config.request_timeout = 15
        self.config.fetch_images = False

    async def scrape_voa_article(self, url: str) -> Optional[Dict]:
        """
        爬取 VOA 文章

        Returns:
            {
                'content': str (纯文本),
                'audio_url': Optional[str]
            }
        """
        logger.info(f"Scraping VOA: {url}")

        try:
            # 并行获取内容和音频
            content_task = self._fetch_content(url)
            audio_task = self._extract_audio_url(url)

            content, audio_url = await asyncio.gather(content_task, audio_task)

            if not content or len(content) < 300:
                logger.warning(f"VOA content too short or empty: {url}")
                return None

            return {
                'content': content,
                'audio_url': audio_url
            }

        except Exception as e:
            logger.error(f"VOA scraping error: {e}")
            return None

    async def _fetch_content(self, url: str) -> Optional[str]:
        """使用 newspaper3k 提取内容"""
        loop = asyncio.get_running_loop()

        def sync_fetch():
            try:
                article = Article(url, config=self.config)
                article.download()
                article.parse()

                content = article.text
                if not content:
                    return None

                # 清洗文本
                content = re.sub(r'(?i)toggle caption\s*', '', content)
                content = re.sub(r'\s+', ' ', content)
                
                # 组合标题
                title = article.title or ""
                if title:
                    content = f"{title}\n\n{content}"

                return content.strip()
            except Exception as e:
                logger.error(f"Content extraction error: {e}")
                return None

        return await loop.run_in_executor(None, sync_fetch)

    async def _extract_audio_url(self, url: str) -> Optional[str]:
        """提取 VOA 音频链接"""
        loop = asyncio.get_running_loop()

        def sync_fetch():
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(url, timeout=10, headers=headers)
                soup = BeautifulSoup(response.text, 'html.parser')

                # 方法 1: audio 标签
                audio = soup.find('audio')
                if audio:
                    source = audio.find('source')
                    if source and source.get('src'):
                        return source['src']

                # 方法 2: data 属性
                player = soup.find('div', {'data-audio-url': True})
                if player:
                    return player.get('data-audio-url')

                # 方法 3: JavaScript 中匹配
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string and 'av.voanews.com' in script.string:
                        match = re.search(
                            r'https://av\.voanews\.com/[^"\'\s]+\.mp3',
                            script.string
                        )
                        if match:
                            return match.group(0)

                logger.debug(f"No audio found for {url}")
                return None

            except Exception as e:
                logger.debug(f"Audio extraction error: {e}")
                return None

        return await loop.run_in_executor(None, sync_fetch)
