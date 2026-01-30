"""
translation：存储中文含义（由deep-translator）。

synonyms：用于存储图表的 JSON 数据。

mistake_count：用于词汇书的单词跟踪。

source_article_id如果您添加的是文章中的单词而不是 CSV 列表中的单词。
"""

class VocabularyItem(Base):
    """
    User's personal vocabulary progress.
    Acts as the 'Vocabulary Book' and 'Daily Learning' storage.
    """
    __tablename__ = 'vocabulary_items'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    word = Column(String(100), nullable=False)
    
    # --- RICH CONTENT (From APIs) ---
    definition = Column(Text)
    translation = Column(String(200))     # Stores the Chinese translation
    example_sentence = Column(Text)       # Stores the example sentence
    image_url = Column(String(500))       # Stores the image link
    audio_url = Column(String(500))       # Optional: for pronunciation audio
    synonyms = Column(JSON)               # Stores the Node/Link data for the Graph
    
    # --- CONTEXT ---
    # If the word came from an article, we link it here. 
    # If it came from the CSV list (Daily Learning), this is Null.
    source_article_id = Column(Integer, ForeignKey('articles.id'), nullable=True)
    
    # --- PROGRESS TRACKING (The "Book" & Quiz Logic) ---
    mistake_count = Column(Integer, default=0)       # Filters for "Vocabulary Book" (Mistakes)
    consecutive_correct = Column(Integer, default=0) # Calculates Spaced Repetition
    next_review_at = Column(DateTime, default=datetime.utcnow) # Determines when to show in Quiz
    is_mastered = Column(Integer, default=0)         # 0 = Learning, 1 = Mastered
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_reviewed = Column(DateTime)
    
    # --- RELATIONSHIPS ---
    user = relationship("User", back_populates="vocabulary_items")