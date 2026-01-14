"""
Data Pipeline 协调器
统一处理所有数据源的文章导入
"""
import asyncio
import json
import logging
from typing import List, Optional

from sqlalchemy.orm import Session

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from models import init_db, get_session, Article, ArticleAnalysis
from .sources import DataSourceFactory, ArticleMetadata
from .scrapers import NewsScraper, VOAScraper
from .text_analyzer import TextAnalyzer
from .llm_analyzer import LLMAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataPipeline:
    """统一数据处理管道"""

    def __init__(
        self,
        sources: List[str] = None,
        enable_llm: bool = True,
        enable_embedding: bool = False,
        target_language: str = "English",
        db_url: str = None
    ):
        """
        初始化 Pipeline

        Args:
            sources: 数据源列表 ['newsapi', 'voa', 'wikipedia']
            enable_llm: 是否启用 LLM 分析
            enable_embedding: 是否启用 embedding（后续开发）
            target_language: LLM 分析目标语言
            db_url: 数据库 URL
        """
        self.sources = sources or ['newsapi', 'voa', 'wikipedia']
        self.enable_llm = enable_llm
        self.enable_embedding = enable_embedding
        self.target_language = target_language

        # 初始化数据库
        self.db_url = db_url or 'sqlite:///backend/english_learning.db'
        self.engine = init_db(self.db_url)

        # 初始化组件
        self.text_analyzer = TextAnalyzer()
        self.news_scraper = NewsScraper()
        self.voa_scraper = VOAScraper()
        
        # LLM 分析器（可选）
        self.llm = None
        if enable_llm:
            try:
                self.llm = LLMAnalyzer()
                logger.info("LLM analyzer enabled")
            except ValueError as e:
                logger.warning(f"LLM disabled: {e}")
                self.enable_llm = False

        logger.info(f"Pipeline initialized with sources: {self.sources}")
        logger.info(f"LLM: {'enabled' if self.enable_llm else 'disabled'}, "
                   f"Embedding: {'enabled' if self.enable_embedding else 'disabled'}")

    async def run(
        self,
        categories: List[str],
        articles_per_category: int = 5
    ) -> dict:
        """
        运行 Pipeline

        Args:
            categories: 类别列表
            articles_per_category: 每个类别的文章数

        Returns:
            统计结果
        """
        stats = {
            'total_fetched': 0,
            'total_scraped': 0,
            'total_analyzed': 0,
            'failed': 0,
            'duplicates': 0
        }

        for source_type in self.sources:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing source: {source_type.upper()}")
            logger.info(f"{'='*60}")

            try:
                # 创建数据源
                source = DataSourceFactory.create(source_type)

                for category in categories:
                    # 检查类别支持
                    if category not in source.get_supported_categories():
                        logger.debug(f"Category '{category}' not supported by {source_type}")
                        continue

                    logger.info(f"\n--- Fetching {category} articles from {source_type} ---")

                    # 1. 获取文章元数据
                    article_metas = source.fetch_articles(category, articles_per_category)
                    stats['total_fetched'] += len(article_metas)
                    logger.info(f"Found {len(article_metas)} articles")

                    # 2. 处理每篇文章
                    for meta in article_metas:
                        result = await self._process_article(meta, source_type)
                        
                        if result == 'success':
                            stats['total_scraped'] += 1
                            if self.enable_llm:
                                stats['total_analyzed'] += 1
                        elif result == 'duplicate':
                            stats['duplicates'] += 1
                        else:
                            stats['failed'] += 1

                        # 避免过快请求
                        await asyncio.sleep(1.5)

            except Exception as e:
                logger.error(f"Error processing source {source_type}: {e}")
                continue

        logger.info(f"\n{'='*60}")
        logger.info(f"Pipeline completed!")
        logger.info(f"Fetched: {stats['total_fetched']}, "
                   f"Scraped: {stats['total_scraped']}, "
                   f"Analyzed: {stats['total_analyzed']}, "
                   f"Failed: {stats['failed']}, "
                   f"Duplicates: {stats['duplicates']}")
        logger.info(f"{'='*60}")

        return stats

    async def _process_article(
        self,
        meta: ArticleMetadata,
        source_type: str
    ) -> str:
        """
        处理单篇文章

        Returns:
            'success', 'duplicate', 'failed'
        """
        session = get_session(self.engine)

        try:
            logger.info(f"\nProcessing: {meta.title[:50]}...")

            # 1. 检查重复
            existing = session.query(Article).filter_by(url=meta.url).first()
            if existing:
                logger.info("  ✗ Duplicate (skipped)")
                return 'duplicate'

            # 2. 爬取内容
            logger.info("  Scraping content...")
            content = None
            audio_url = None

            if source_type == 'voa':
                result = await self.voa_scraper.scrape_voa_article(meta.url)
                if result:
                    content = result['content']
                    audio_url = result.get('audio_url')
            elif source_type == 'wikipedia':
                # Wikipedia 直接从 API 获取内容
                content = await self._fetch_wikipedia_content(meta.url)
            else:
                content = await self.news_scraper.scrape_article(meta.url)

            if not content:
                logger.warning("  ✗ Scraping failed")
                return 'failed'

            # 3. 文本分析
            logger.info("  Analyzing text...")
            analysis = self.text_analyzer.analyze(content)

            # 4. 保存 Article
            article = Article(
                title=meta.title,
                content=content,
                url=meta.url,
                source=meta.source,
                source_name=meta.source_name,
                category=meta.category,
                published_at=meta.published_at,
                audio_url=audio_url,
                difficulty_level=analysis['difficulty_level'],
                difficulty_score=analysis['difficulty_score'],
                word_count=analysis['word_count'],
                sentence_count=analysis['sentence_count'],
                avg_sentence_length=analysis['avg_sentence_length'],
                unique_words=analysis['unique_words'],
                key_words=analysis['key_words']
            )

            session.add(article)
            session.flush()

            logger.info(f"  ✓ Article saved (ID: {article.id}, Level: {analysis['difficulty_level']})")

            # 5. LLM 分析（可选）
            if self.enable_llm and self.llm:
                logger.info("  Analyzing with LLM...")

                try:
                    llm_result = await self.llm.analyze_article(
                        content,
                        target_language=self.target_language,
                        difficulty_level=analysis['difficulty_level'],
                        word_count=analysis['word_count']
                    )

                    if llm_result:
                        article_analysis = ArticleAnalysis(
                            article_id=article.id,
                            target_language=self.target_language,
                            summary=llm_result.summary,
                            analysis_data=llm_result.model_dump(
                                mode='json',
                                exclude={'summary'}
                            )
                        )
                        session.add(article_analysis)
                        logger.info("  ✓ LLM analysis saved")
                    else:
                        logger.warning("  ✗ LLM analysis returned empty")

                except Exception as e:
                    logger.error(f"  ✗ LLM error: {e}")

            session.commit()
            return 'success'

        except Exception as e:
            logger.error(f"  ✗ Error: {e}")
            session.rollback()
            return 'failed'

        finally:
            session.close()

    async def _fetch_wikipedia_content(self, url: str) -> Optional[str]:
        """获取 Wikipedia 文章内容"""
        import wikipedia
        
        loop = asyncio.get_running_loop()
        
        def sync_fetch():
            try:
                # 从 URL 提取标题
                title = url.split('/wiki/')[-1].replace('_', ' ')
                page = wikipedia.page(title, auto_suggest=False)
                return f"{page.title}\n\n{page.summary}"
            except Exception as e:
                logger.error(f"Wikipedia fetch error: {e}")
                return None
        
        return await loop.run_in_executor(None, sync_fetch)

if __name__ == "__main__":
    import argparse
    from dotenv import load_dotenv # Load env
    
    load_dotenv()
    
    parser = argparse.ArgumentParser(description='Data Ingestion Pipeline')
    parser.add_argument('--limit', type=int, default=3, help='Limit articles per category')
    parser.add_argument('--sources', type=str, default='all', help='Sources (comma-separated: voa,wikipedia,newsapi)')
    parser.add_argument('--llm', action='store_true', default=True, help='Enable LLM analysis')
    parser.add_argument('--no-llm', action='store_false', dest='llm', help='Disable LLM analysis')
    
    args = parser.parse_args()
    
    sources = args.sources.split(',') if args.sources != 'all' else None
    
    pipeline = DataPipeline(
        sources=sources, # Fix source passing
        enable_llm=args.llm,
        target_language="English"
    )
    
    # Run simply with some default categories
    asyncio.run(pipeline.run(
        categories=['Technology', 'Science', 'Health'], # Run some default categories
        articles_per_category=args.limit
    ))
