"""
数据库模型定义
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, ForeignKey, Table, JSON, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

# 用户兴趣标签关联表
user_interests = Table('user_interests', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('topic', String(50))
)

class User(Base):
    """用户模型"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True)
    password_hash = Column(String(200))  # 简化版本，实际应该加密
    
    # 用户基本信息
    english_level = Column(String(10))  # A1, A2, B1, B2, C1, C2
    learning_goal = Column(String(50))  # exam, business, travel, general
    estimated_vocabulary = Column(Integer, default=0)
    
    # 用户画像
    interests = Column(JSON)  # {"technology": 0.4, "entertainment": 0.2, ...}
    user_embedding = Column(Text)  # JSON string of user's interest vector
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    reading_history = relationship("ReadingHistory", back_populates="user")
    vocabulary_items = relationship("VocabularyItem", back_populates="user")
    writing_history = relationship("WritingHistory", back_populates="user")
    speaking_history = relationship("SpeakingHistory", back_populates="user")

class Article(Base):
    """文章模型"""
    __tablename__ = 'articles'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String(500), unique=True)  # 唯一约束防止重复
    
    # 数据源
    source = Column(String(100))  # 'newsapi', 'voa', 'wikipedia'
    source_name = Column(String(100))  # 具体来源（如 'BBC', 'CNN'）
    category = Column(String(50))  # technology, science, etc.
    published_at = Column(DateTime, nullable=True)  # 发布时间
    
    # 文本分析
    difficulty_level = Column(String(10))  # A1-C2
    difficulty_score = Column(Float)  # 0-100
    word_count = Column(Integer)
    sentence_count = Column(Integer)
    avg_sentence_length = Column(Float)
    unique_words = Column(Integer)
    
    # 推荐系统（后续启用）
    embedding = Column(Text)  # JSON 字符串
    key_words = Column(JSON)
    
    # 统计信息
    views = Column(Integer, default=0)
    avg_completion_rate = Column(Float, default=0.0)
    
    # VOA 特定
    audio_url = Column(String(500), nullable=True)  # 预留音频

    # AI/Generated image
    image_url = Column(String(500), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    reading_history = relationship("ReadingHistory", back_populates="article")
    analyses = relationship("ArticleAnalysis", back_populates="article", cascade="all, delete-orphan")


class ArticleAnalysis(Base):
    """LLM 深度分析结果"""
    __tablename__ = 'article_analyses'
    
    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('articles.id', ondelete='CASCADE'), nullable=False)
    target_language = Column(String(50), default='English')
    
    # 分析结果
    summary = Column(Text)  # 摘要
    analysis_data = Column(JSON, nullable=False)
    # analysis_data 结构:
    # {
    #   "vocabulary": [{"word": "...", "pronunciation": "...", "definition": "..."}],
    #   "collocations": [{"phrase": "...", "meaning": "...", "usage_tag": "..."}],
    #   "sentence_patterns": [{"skeleton": "...", "explanation": "...", "source_sentence": "..."}]
    # }
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 唯一约束：每篇文章每种语言只有一个分析
    __table_args__ = (
        UniqueConstraint('article_id', 'target_language', name='uix_article_lang'),
    )
    
    # 关系
    article = relationship("Article", back_populates="analyses")

class ArticleTranslation(Base):
    """文章翻译"""
    __tablename__ = 'article_translations'

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('articles.id', ondelete='CASCADE'), nullable=False)
    target_language = Column(String(50), default='zh-CN')
    translation_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('article_id', 'target_language', name='uix_article_translation_lang'),
    )

    article = relationship("Article", backref="translations")

class ReadingHistory(Base):
    """阅读历史"""
    __tablename__ = 'reading_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    article_id = Column(Integer, ForeignKey('articles.id'), nullable=False)
    
    # 阅读行为
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime)
    completion_rate = Column(Float)  # 0.0 - 1.0
    time_spent = Column(Integer)  # seconds
    
    # 用户反馈
    liked = Column(Integer, default=0)  # -1: dislike, 0: neutral, 1: like
    bookmarked = Column(Integer, default=0)
    
    # 学习数据
    words_looked_up = Column(JSON)  # List of words user looked up
    quiz_score = Column(Float)  # If they took a quiz
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="reading_history")
    article = relationship("Article", back_populates="reading_history")

class VocabularyItem(Base):
    """用户生词本"""
    __tablename__ = 'vocabulary_items'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    word = Column(String(100), nullable=False)
    
    # 词汇信息
    definition = Column(Text)
    example_sentence = Column(Text)
    translation = Column(Text)
    example_translation = Column(Text)
    source_article_id = Column(Integer, ForeignKey('articles.id'))
    
    # 学习进度
    times_reviewed = Column(Integer, default=0)
    mastery_level = Column(Integer, default=0)  # 0-5
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_reviewed = Column(DateTime)
    
    # 关系
    user = relationship("User", back_populates="vocabulary_items")

class StandardVocabulary(Base):
    """标准词库"""
    __tablename__ = 'standard_vocabulary'

    id = Column(Integer, primary_key=True)
    list_name = Column(String(50))
    word = Column(String(100), nullable=False)
    definition = Column(Text)

class WritingHistory(Base):
    """写作历史记录"""
    __tablename__ = 'writing_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # 写作内容
    topic = Column(String(200))
    text = Column(Text, nullable=False)
    word_count = Column(Integer)
    
    # 评分结果
    ielts_overall = Column(Float)
    ielts_task_response = Column(Float)
    ielts_coherence = Column(Float)
    ielts_lexical = Column(Float)
    ielts_grammar = Column(Float)
    
    general_overall = Column(Float)
    
    # 完整评估数据（JSON格式保存所有反馈）
    evaluation_data = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="writing_history")

class SpeakingHistory(Base):
    """口语历史记录"""
    __tablename__ = 'speaking_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # 口语内容
    transcription = Column(Text)
    duration = Column(Float)  # seconds
    
    # 评分结果
    overall_band = Column(Float)
    fluency_score = Column(Float)
    vocabulary_score = Column(Float)
    grammar_score = Column(Float)
    
    # 完整评估数据
    evaluation_data = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="speaking_history")

def init_db(db_url='sqlite:///backend/english_learning.db'):
    """初始化数据库"""
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    return engine

def get_session(engine):
    """获取数据库会话"""
    Session = sessionmaker(bind=engine)
    return Session()
