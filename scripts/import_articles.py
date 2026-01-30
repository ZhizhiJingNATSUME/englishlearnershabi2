"""
文章导入脚本 - 从维基百科抓取和处理文章
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from backend.models import init_db, get_session, Article
from backend.content_processor import ContentProcessor

def import_articles(clear_existing=False):
    """导入文章到数据库"""
    
    # 定义要抓取的主题
    topics = [
        'Technology',
        'Science',
        'History',
        'Geography',
        'Health',
        'Sports',
        'Arts',
        'Music',
        'Literature',
        'Business'
    ]
    
    # 清理现有文章（可选）
    if clear_existing:
        print("\n⚠️  Clearing existing articles from database...")
        engine = init_db()
        session = get_session(engine)
        try:
            deleted_count = session.query(Article).delete()
            session.commit()
            print(f"✓ Deleted {deleted_count} existing articles\n")
        except Exception as e:
            print(f"✗ Error clearing articles: {e}")
            session.rollback()
        finally:
            session.close()
    
    print("=" * 70)
    print("IMPROVED ARTICLE IMPORT - Fetching Specific Topics")
    print("=" * 70)
    print("\nInitializing content processor...")
    processor = ContentProcessor()
    
    print(f"\nCategories to fetch: {', '.join(topics)}")
    print("Count per category: 3 articles")
    print("\nThis may take a few minutes...")
    print("-" * 70)
    
    # 从维基百科抓取文章（使用改进的方法）
    raw_articles = processor.fetch_wikipedia_articles(topics, count_per_topic=3)
    
    print(f"\nFetched {len(raw_articles)} articles")
    print("\nProcessing articles...")
    
    # 处理文章
    processed_articles = processor.batch_process_articles(raw_articles)
    
    print(f"\nSuccessfully processed {len(processed_articles)} articles")
    
    # 保存到数据库
    print("\nSaving articles to database...")
    
    engine = init_db()
    session = get_session(engine)
    
    saved_count = 0
    
    try:
        for article_data in processed_articles:
            # 检查是否已存在
            existing = session.query(Article).filter_by(title=article_data['title']).first()
            if existing:
                print(f"  Article already exists: {article_data['title']}")
                continue
            
            # 创建文章对象
            article = Article(
                title=article_data['title'],
                content=article_data['content'],
                source=article_data['source'],
                url=article_data['url'],
                category=article_data['category'],
                difficulty_level=article_data['difficulty_level'],
                difficulty_score=article_data['difficulty_score'],
                word_count=article_data['word_count'],
                sentence_count=article_data['sentence_count'],
                avg_sentence_length=article_data['avg_sentence_length'],
                unique_words=article_data['unique_words'],
                key_words=article_data['key_words'],
                embedding=json.dumps(article_data['embedding'])
            )
            
            session.add(article)
            saved_count += 1
            print(f"  Saved: {article_data['title']} (Level: {article_data['difficulty_level']})")
        
        session.commit()
        print(f"\n✓ Successfully saved {saved_count} new articles to database")
        
    except Exception as e:
        session.rollback()
        print(f"\n✗ Error saving articles: {e}")
    finally:
        session.close()
    
    # 显示统计信息
    session = get_session(engine)
    try:
        total_count = session.query(Article).count()
        print(f"\nTotal articles in database: {total_count}")
        
        # 按难度统计
        print("\nArticles by difficulty level:")
        for level in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
            count = session.query(Article).filter_by(difficulty_level=level).count()
            if count > 0:
                print(f"  {level}: {count}")
        
        # 按类别统计
        print("\nArticles by category:")
        categories = session.query(Article.category).distinct().all()
        for (cat,) in categories:
            count = session.query(Article).filter_by(category=cat).count()
            print(f"  {cat}: {count}")
            
    finally:
        session.close()

if __name__ == '__main__':
    import sys
    
    # 检查是否需要清理现有文章
    clear_existing = '--clear' in sys.argv or '-c' in sys.argv
    
    if clear_existing:
        print("\n⚠️  WARNING: This will delete all existing articles!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Operation cancelled.")
            sys.exit(0)
    
    import_articles(clear_existing=clear_existing)

