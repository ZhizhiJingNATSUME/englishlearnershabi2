#!/usr/bin/env python3
"""
Analyze all articles that are missing LLM analysis
"""
import sys
import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Load environment variables
load_dotenv()

from backend.models import Article, ArticleAnalysis, init_db, get_session
from backend.data_pipeline.llm_analyzer import LLMAnalyzer

async def analyze_missing_articles(dry_run=False, limit=None):
    """Analyze articles that don't have LLM analysis"""
    
    # Initialize
    engine = init_db()
    session = get_session(engine)
    analyzer = LLMAnalyzer()
    
    try:
        # Get articles without analysis
        articles_without_analysis = session.query(Article)\
            .outerjoin(ArticleAnalysis, Article.id == ArticleAnalysis.article_id)\
            .filter(ArticleAnalysis.id == None)\
            .all()
        
        total = len(articles_without_analysis)
        print(f"\n📊 Found {total} articles without LLM analysis")
        
        if total == 0:
            print("✅ All articles already have analysis!")
            return
        
        if dry_run:
            print("\n🔍 DRY RUN - No changes will be made")
            print("\nArticles that would be analyzed:")
            for i, article in enumerate(articles_without_analysis[:limit] if limit else articles_without_analysis, 1):
                print(f"{i}. [{article.id}] {article.title[:80]} - {article.category} - {article.source}")
            return
        
        # Limit articles if specified
        articles_to_analyze = articles_without_analysis[:limit] if limit else articles_without_analysis
        print(f"\n🔄 Analyzing {len(articles_to_analyze)} articles...")
        print("=" * 80)
        
        success_count = 0
        error_count = 0
        quota_exceeded = False
        
        for i, article in enumerate(articles_to_analyze, 1):
            if quota_exceeded:
                print(f"\n⚠️ Skipping remaining articles due to quota limit")
                break
                
            print(f"\n[{i}/{len(articles_to_analyze)}] Analyzing Article ID {article.id}")
            print(f"   Title: {article.title[:80]}...")
            print(f"   Category: {article.category} | Source: {article.source} | Level: {article.difficulty_level}")
            
            try:
                # Check if article has content
                if not article.content or len(article.content.strip()) < 100:
                    print(f"   ⚠️ Skipped - Content too short ({len(article.content) if article.content else 0} chars)")
                    error_count += 1
                    continue
                
                # Run LLM analysis
                print(f"   🤖 Running LLM analysis...")
                analysis_data = await analyzer.analyze_article(
                    content=article.content,
                    target_language='English'
                )
                
                if not analysis_data:
                    print(f"   ❌ Analysis failed - No data returned")
                    error_count += 1
                    continue
                
                # Save to database
                article_analysis = ArticleAnalysis(
                    article_id=article.id,
                    target_language='English',
                    summary=analysis_data.get('summary', ''),
                    analysis_data=analysis_data
                )
                
                session.add(article_analysis)
                session.commit()
                
                print(f"   ✅ Analysis saved successfully")
                print(f"      - Vocabulary: {len(analysis_data.get('vocabulary', []))} items")
                print(f"      - Collocations: {len(analysis_data.get('collocations', []))} items")
                print(f"      - Grammar: {len(analysis_data.get('grammar_points', []))} items")
                
                success_count += 1
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(2)
                
            except Exception as e:
                error_msg = str(e)
                print(f"   ❌ Error: {error_msg}")
                
                # Check if it's a quota error
                if '429' in error_msg or 'quota' in error_msg.lower() or 'rate limit' in error_msg.lower():
                    print(f"   ⚠️ API quota exceeded - stopping analysis")
                    quota_exceeded = True
                    error_count += 1
                    break
                
                error_count += 1
                session.rollback()
                
                # Continue with next article
                continue
        
        print("\n" + "=" * 80)
        print(f"\n📊 Analysis Complete!")
        print(f"   ✅ Success: {success_count}")
        print(f"   ❌ Errors: {error_count}")
        print(f"   📝 Remaining: {total - success_count - error_count}")
        
        if quota_exceeded:
            print(f"\n⚠️ API quota limit reached. Run this script again later to continue.")
        
    finally:
        session.close()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze articles missing LLM analysis')
    parser.add_argument('--dry-run', action='store_true', 
                      help='Show what would be analyzed without making changes')
    parser.add_argument('--limit', type=int, 
                      help='Limit number of articles to analyze')
    
    args = parser.parse_args()
    
    print("\n" + "=" * 80)
    print("🔬 Article Analysis Tool")
    print("=" * 80)
    
    # Run async function
    asyncio.run(analyze_missing_articles(
        dry_run=args.dry_run,
        limit=args.limit
    ))

if __name__ == '__main__':
    main()

