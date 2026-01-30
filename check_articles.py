import sys
import os
sys.path.insert(0, 'backend')

from models import init_db, Article
from sqlalchemy.orm import sessionmaker

engine = init_db('sqlite:///backend/english_learning.db')
Session = sessionmaker(bind=engine)
session = Session()

articles = session.query(Article).all()
print(f'\n📚 数据库中有 {len(articles)} 篇文章\n')

for i, article in enumerate(articles, 1):
    print(f'{i}. {article.title}')
    print(f'   级别: {article.difficulty_level} | 字数: {article.word_count}')
    print(f'   来源: {article.source}')
    print()

session.close()
