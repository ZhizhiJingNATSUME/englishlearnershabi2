#!/usr/bin/env python3
"""
Backfill Embeddings Script
为数据库中已存在的文章生成embeddings

Usage:
    python scripts/backfill_embeddings.py [--batch-size 50] [--force]

Options:
    --batch-size: 每批处理的文章数量 (default: 50)
    --force: 强制重新生成所有embeddings（包括已有的）
    --dry-run: 只显示将要处理的文章，不实际生成
"""
import os
import sys
import json
import argparse
import logging
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend'))

from backend.models import init_db, get_session, Article
from backend.embedding_service import generate_article_embedding, generate_batch_embeddings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def backfill_embeddings(
    db_url: str = None,
    batch_size: int = 50,
    force: bool = False,
    dry_run: bool = False
):
    """
    为数据库中的文章生成embeddings
    
    Args:
        db_url: 数据库URL
        batch_size: 每批处理数量
        force: 是否强制重新生成
        dry_run: 是否只预览
    """
    # 初始化数据库
    db_url = db_url or 'sqlite:///backend/english_learning.db'
    engine = init_db(db_url)
    session = get_session(engine)
    
    try:
        # 查询需要处理的文章
        query = session.query(Article)
        
        if not force:
            # 只处理没有embedding的文章
            query = query.filter(
                (Article.embedding == None) | (Article.embedding == '')
            )
        
        total_count = query.count()
        
        if total_count == 0:
            logger.info("No articles need embedding generation!")
            return
        
        logger.info(f"Found {total_count} articles to process")
        
        if dry_run:
            logger.info("Dry run mode - showing first 10 articles:")
            for article in query.limit(10).all():
                logger.info(f"  - [{article.id}] {article.title[:50]}...")
            return
        
        # 分批处理
        processed = 0
        failed = 0
        
        while True:
            # 获取一批文章
            articles = query.limit(batch_size).all()
            
            if not articles:
                break
            
            logger.info(f"Processing batch: {processed + 1} - {processed + len(articles)} / {total_count}")
            
            # 为每篇文章生成embedding
            for article in articles:
                try:
                    # 准备关键词
                    key_words = []
                    if article.key_words:
                        if isinstance(article.key_words, str):
                            key_words = json.loads(article.key_words)
                        else:
                            key_words = article.key_words
                    
                    # 生成embedding
                    embedding = generate_article_embedding(
                        title=article.title,
                        content=article.content or '',
                        category=article.category or '',
                        key_words=key_words
                    )
                    
                    if embedding:
                        article.embedding = json.dumps(embedding)
                        processed += 1
                        
                        if processed % 10 == 0:
                            logger.info(f"  Processed {processed} articles...")
                    else:
                        logger.warning(f"  Failed to generate embedding for article {article.id}")
                        failed += 1
                        
                except Exception as e:
                    logger.error(f"  Error processing article {article.id}: {e}")
                    failed += 1
            
            # 提交这批的更改
            session.commit()
            
            # 重新查询（因为已处理的文章可能已经有embedding了）
            if not force:
                query = session.query(Article).filter(
                    (Article.embedding == None) | (Article.embedding == '')
                )
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Backfill completed!")
        logger.info(f"  Processed: {processed}")
        logger.info(f"  Failed: {failed}")
        logger.info(f"{'='*60}")
        
    except Exception as e:
        logger.error(f"Error during backfill: {e}")
        session.rollback()
        raise
        
    finally:
        session.close()


def verify_embeddings(db_url: str = None):
    """
    验证embedding生成结果
    """
    db_url = db_url or 'sqlite:///backend/english_learning.db'
    engine = init_db(db_url)
    session = get_session(engine)
    
    try:
        total = session.query(Article).count()
        with_embedding = session.query(Article).filter(
            Article.embedding != None,
            Article.embedding != ''
        ).count()
        
        logger.info(f"\nEmbedding Statistics:")
        logger.info(f"  Total articles: {total}")
        logger.info(f"  With embeddings: {with_embedding}")
        logger.info(f"  Without embeddings: {total - with_embedding}")
        logger.info(f"  Coverage: {with_embedding/total*100:.1f}%" if total > 0 else "  Coverage: N/A")
        
        # 检查embedding维度
        sample = session.query(Article).filter(
            Article.embedding != None,
            Article.embedding != ''
        ).first()
        
        if sample and sample.embedding:
            try:
                emb = json.loads(sample.embedding)
                logger.info(f"  Embedding dimension: {len(emb)}")
            except:
                pass
                
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Backfill article embeddings')
    parser.add_argument('--batch-size', type=int, default=50, help='Batch size for processing')
    parser.add_argument('--force', action='store_true', help='Force regenerate all embeddings')
    parser.add_argument('--dry-run', action='store_true', help='Preview without making changes')
    parser.add_argument('--verify', action='store_true', help='Only verify current embedding status')
    parser.add_argument('--db-url', type=str, default=None, help='Database URL')
    
    args = parser.parse_args()
    
    if args.verify:
        verify_embeddings(args.db_url)
    else:
        backfill_embeddings(
            db_url=args.db_url,
            batch_size=args.batch_size,
            force=args.force,
            dry_run=args.dry_run
        )
        # 完成后验证
        verify_embeddings(args.db_url)

