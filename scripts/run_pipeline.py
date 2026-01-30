#!/usr/bin/env python3
"""
Data Pipeline 启动脚本
运行：python scripts/run_pipeline.py --help
"""
import asyncio
import argparse
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from backend.data_pipeline import DataPipeline

# Standardized 8 categories (all lowercase)
STANDARD_CATEGORIES = ['technology', 'science', 'health', 'business', 'education', 'culture', 'sports', 'entertainment']

# Available categories by source (mapped to standard 8)
AVAILABLE_CATEGORIES = {
    'newsapi': ['technology', 'science', 'health', 'business', 'sports', 'entertainment'],
    'voa': ['science', 'health', 'education', 'culture', 'entertainment'],
    'wikipedia': ['technology', 'science', 'health', 'business', 'education', 'culture', 'sports', 'entertainment']
}


def main():
    parser = argparse.ArgumentParser(
        description="Run data pipeline to fetch and analyze articles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 基础使用（所有数据源，默认分类）
  python scripts/run_pipeline.py

  # 指定数据源
  python scripts/run_pipeline.py --sources newsapi voa

  # 指定分类（使用小写）
  python scripts/run_pipeline.py --categories technology science health

  # 获取更多分类
  python scripts/run_pipeline.py --categories technology science health business education culture

  # 快速测试（不使用 LLM）
  python scripts/run_pipeline.py --no-llm --count 2

  # 指定目标语言
  python scripts/run_pipeline.py --language "Chinese (Simplified)"

Standardized 8 Categories (all lowercase):
  technology, science, health, business, education, culture, sports, entertainment

Available by Source:
  NewsAPI:    technology, science, health, business, sports, entertainment (6/8)
  VOA:        science, health, education, culture, entertainment (5/8)
  Wikipedia:  All 8 categories supported
        """
    )

    parser.add_argument(
        '--sources',
        nargs='+',
        default=['newsapi', 'voa', 'wikipedia'],
        choices=['newsapi', 'voa', 'wikipedia'],
        help='Data sources to process (default: all)'
    )

    parser.add_argument(
        '--categories',
        nargs='+',
        default=['technology', 'science', 'health'],
        help='Categories to fetch from: technology, science, health, business, education, culture, sports, entertainment'
    )

    parser.add_argument(
        '--count',
        type=int,
        default=5,
        help='Articles per category per source (default: 5)'
    )

    parser.add_argument(
        '--no-llm',
        action='store_true',
        help='Disable LLM analysis (faster, for testing)'
    )

    parser.add_argument(
        '--no-embedding',
        action='store_true',
        help='Disable embedding generation (default: enabled)'
    )

    parser.add_argument(
        '--language',
        default='English',
        help='Target language for LLM analysis (default: English)'
    )

    parser.add_argument(
        '--db-url',
        default=None,
        help='Database URL (default: sqlite:///backend/english_learning.db)'
    )

    args = parser.parse_args()

    # 检查环境变量
    if 'newsapi' in args.sources and not os.getenv('NEWS_API_KEY'):
        print("⚠️  WARNING: NEWS_API_KEY not set, NewsAPI source will fail")
    
    if not args.no_llm and not os.getenv('GEMINI_API_KEY'):
        print("⚠️  WARNING: GEMINI_API_KEY not set, LLM analysis will be disabled")

    # Normalize categories to lowercase
    categories = [c.lower() for c in args.categories]
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    Data Pipeline                              ║
╠══════════════════════════════════════════════════════════════╣
║  Sources:     {', '.join(args.sources):<44} ║
║  Categories:  {', '.join(categories):<44} ║
║  Count:       {args.count} per category{' ':<33} ║
║  LLM:         {'Disabled' if args.no_llm else 'Enabled':<44} ║
║  Embedding:   {'Disabled' if args.no_embedding else 'Enabled':<44} ║
║  Language:    {args.language:<44} ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # 创建 Pipeline
    pipeline = DataPipeline(
        sources=args.sources,
        enable_llm=not args.no_llm,
        enable_embedding=not args.no_embedding,
        target_language=args.language,
        db_url=args.db_url
    )

    # 运行
    stats = asyncio.run(pipeline.run(
        categories=categories,  # Use normalized lowercase categories
        articles_per_category=args.count
    ))

    # 输出统计
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    Results                                    ║
╠══════════════════════════════════════════════════════════════╣
║  Fetched:     {stats['total_fetched']:<44} ║
║  Scraped:     {stats['total_scraped']:<44} ║
║  Analyzed:    {stats['total_analyzed']:<44} ║
║  Embedded:    {stats.get('total_embedded', 0):<44} ║
║  Duplicates:  {stats['duplicates']:<44} ║
║  Failed:      {stats['failed']:<44} ║
╚══════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    main()
