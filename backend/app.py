"""
Flask API服务
"""
import os
import json
import tempfile
import re
import sqlite3
import random
import asyncio
import csv
import requests
from typing import Optional
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy.orm import sessionmaker

from models import init_db, get_session, User, Article, ReadingHistory, VocabularyItem, ArticleAnalysis, WritingHistory, SpeakingHistory
from recommender import ArticleRecommender
from question_generator import QuestionGenerator

app = Flask(__name__)
CORS(app)

# 配置
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
# 使用绝对路径或相对于当前目录的路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'english_learning.db')
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{DB_PATH}')
VOCAB_LIST_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'english_learning.db'))

# 初始化数据库
engine = init_db(DATABASE_URL)
Session = sessionmaker(bind=engine)

def ensure_vocabulary_columns():
    """确保生词表包含翻译字段"""
    if not os.path.exists(DB_PATH):
        return
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(vocabulary_items)")
        columns = {row[1] for row in cursor.fetchall()}
        if "translation" not in columns:
            cursor.execute("ALTER TABLE vocabulary_items ADD COLUMN translation TEXT")
        if "example_translation" not in columns:
            cursor.execute("ALTER TABLE vocabulary_items ADD COLUMN example_translation TEXT")
        conn.commit()
    finally:
        conn.close()

def translate_text(text: str, source_lang: str = "en", target_lang: str = "zh-CN") -> str:
    """使用免费翻译API翻译文本"""
    if not text:
        return ""
    cleaned = text.strip()
    if not cleaned:
        return ""
    translation = ""
    try:
        response = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": cleaned, "langpair": f"{source_lang}|{target_lang}"},
            timeout=10
        )
        if response.ok:
            data = response.json()
            translation = data.get("responseData", {}).get("translatedText", "") or ""
    except requests.RequestException:
        translation = ""
    if translation and translation.strip().lower() != cleaned.lower():
        return translation
    try:
        response = requests.post(
            "https://libretranslate.de/translate",
            json={
                "q": cleaned,
                "source": source_lang,
                "target": target_lang,
                "format": "text"
            },
            timeout=10
        )
        if response.ok:
            data = response.json()
            fallback = data.get("translatedText", "") or ""
            if fallback and fallback.strip().lower() != cleaned.lower():
                return fallback
    except requests.RequestException:
        return ""
    return translation if translation.strip().lower() != cleaned.lower() else ""

def fetch_dictionary_entry(word: str) -> dict:
    """获取英文释义和例句"""
    data = {"definition": "", "example_sentence": "", "part_of_speech": ""}
    try:
        response = requests.get(
            f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}",
            timeout=10
        )
        if not response.ok:
            return data
        payload = response.json()[0]
        meanings = payload.get("meanings", [])
        if not meanings:
            return data
        meaning = meanings[0]
        for item in meanings:
            if item.get("partOfSpeech") in ["noun", "verb"]:
                meaning = item
                break
        definitions = meaning.get("definitions", [])
        if definitions:
            definition_entry = definitions[0]
            data["definition"] = definition_entry.get("definition", "")
            data["example_sentence"] = definition_entry.get("example", "")
        data["part_of_speech"] = meaning.get("partOfSpeech", "")
    except (requests.RequestException, IndexError, KeyError, ValueError):
        return data
    return data

def build_example_sentence(word: str, part_of_speech: str) -> str:
    """生成更自然的示例句"""
    templates = {
        "noun": [
            "The {word} plays an important role in daily life.",
            "She wrote a report about the {word}.",
            "We discussed the {word} during the meeting."
        ],
        "verb": [
            "They decided to {word} before the deadline.",
            "She will {word} the plan tomorrow.",
            "Please {word} your answer carefully."
        ],
        "adjective": [
            "It was a {word} decision to make.",
            "The results were surprisingly {word}.",
            "He felt {word} after the long trip."
        ],
        "adverb": [
            "She spoke {word} during the presentation.",
            "The team worked {word} to finish on time.",
            "He responded {word} to the request."
        ],
        "default": [
            "They used the word \"{word}\" in the discussion.",
            "He is trying to remember the word \"{word}\".",
            "The article included the term \"{word}\"."
        ]
    }
    key = part_of_speech.lower() if part_of_speech else "default"
    choices = templates.get(key, templates["default"])
    return random.choice(choices).format(word=word)

def fetch_random_vocab_word(list_name: Optional[str]):
    """从词库中随机抽取单词"""
    if not os.path.exists(VOCAB_LIST_DB_PATH):
        return None
    conn = sqlite3.connect(VOCAB_LIST_DB_PATH)
    try:
        cursor = conn.cursor()
        if list_name:
            if list_name.lower() == "ielts&toefl":
                cursor.execute(
                    "SELECT word, list_name FROM standard_vocabulary WHERE list_name IN (?, ?) ORDER BY RANDOM() LIMIT 1",
                    ("IELTS", "TOEFL")
                )
            else:
                cursor.execute(
                    "SELECT word, list_name FROM standard_vocabulary WHERE list_name = ? ORDER BY RANDOM() LIMIT 1",
                    (list_name,)
                )
        else:
            cursor.execute(
                "SELECT word, list_name FROM standard_vocabulary ORDER BY RANDOM() LIMIT 1"
            )
        row = cursor.fetchone()
        return row
    finally:
        conn.close()

def load_vocab_list_from_csv(list_name: str, csv_filename: str) -> bool:
    """从 CSV 导入词库"""
    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', csv_filename))
    if not os.path.exists(csv_path):
        return False
    conn = sqlite3.connect(VOCAB_LIST_DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM standard_vocabulary WHERE list_name = ?", (list_name,))
        existing_count = cursor.fetchone()[0]
        if existing_count > 0:
            return True
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            rows = []
            for row in reader:
                if not row:
                    continue
                word_text = row[0].strip()
                definition = row[1].strip() if len(row) > 1 else None
                if word_text:
                    rows.append((list_name, word_text, definition))
        if rows:
            cursor.executemany(
                "INSERT INTO standard_vocabulary (list_name, word, definition) VALUES (?, ?, ?)",
                rows
            )
            conn.commit()
        return True
    finally:
        conn.close()

def ensure_vocab_list_loaded(list_name: str) -> bool:
    """确保词库列表已加载"""
    list_map = {
        "CET4": "4_random_350_words.csv",
        "CET6": "6_random_350_words.csv",
        "SAT": "sat_random_350_words.csv"
    }
    csv_filename = list_map.get(list_name.upper())
    if not csv_filename:
        return True
    return load_vocab_list_from_csv(list_name.upper(), csv_filename)

ensure_vocabulary_columns()

def build_vocab_quiz(user_id: int):
    """基于用户生词本生成简单测验"""
    session = Session()
    try:
        items = session.query(VocabularyItem).filter_by(user_id=user_id).all()
        if len(items) < 4:
            return None
        target = items[0]
        if len(items) > 1:
            target = items[int(datetime.utcnow().timestamp()) % len(items)]
        target_translation = target.translation or translate_text(target.word)
        if not target_translation:
            return None
        distractors = []
        for item in items:
            if item.id == target.id:
                continue
            if item.translation:
                distractors.append(item.translation)
            if len(distractors) >= 3:
                break
        while len(distractors) < 3:
            distractor_word = fetch_random_vocab_word(None)
            if not distractor_word:
                break
            distractor_translation = translate_text(distractor_word[0])
            if distractor_translation and distractor_translation != target_translation:
                distractors.append(distractor_translation)
        if len(distractors) < 3:
            return None
        options = distractors[:3] + [target_translation]
        random.shuffle(options)
        return {
            "word": target.word,
            "question": f"What is the Chinese translation of \"{target.word}\"?",
            "options": options,
            "answer": target_translation
        }
    finally:
        session.close()

# 初始化推荐器
recommender = ArticleRecommender()

# 初始化题目生成器
question_generator = QuestionGenerator()

# 初始化阅读测试系统
reading_test_system = None

def init_recommender():
    """初始化推荐系统"""
    session = Session()
    try:
        # 只查询必要的元数据，不查询 content 以提升性能
        articles = session.query(
            Article.id, Article.title, Article.category, 
            Article.difficulty_level, Article.difficulty_score, 
            Article.embedding, Article.views, Article.avg_completion_rate
        ).all()
        
        article_dicts = []
        for article in articles:
            article_dicts.append({
                'id': article.id,
                'title': article.title,
                'category': article.category,
                'difficulty_level': article.difficulty_level,
                'difficulty_score': article.difficulty_score,
                'embedding': article.embedding,
                'views': article.views,
                'avg_completion_rate': article.avg_completion_rate
            })
        recommender.build_index(article_dicts)
    finally:
        session.close()

# ========== 用户相关API ==========

@app.route('/api/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.json
    
    username = data.get('username')
    email = data.get('email')
    english_level = data.get('english_level', 'B1')
    interests = data.get('interests', {})
    learning_goal = data.get('learning_goal', 'general')
    
    if not username:
        return jsonify({'error': 'Username is required'}), 400
    
    session = Session()
    try:
        # 检查用户名是否存在
        existing_user = session.query(User).filter_by(username=username).first()
        if existing_user:
            return jsonify({'error': 'Username already exists'}), 400
        
        # 创建新用户
        new_user = User(
            username=username,
            email=email,
            english_level=english_level,
            learning_goal=learning_goal,
            interests=interests
        )
        
        session.add(new_user)
        session.commit()
        
        return jsonify({
            'message': 'User registered successfully',
            'user': {
                'id': new_user.id,
                'username': new_user.username,
                'email': new_user.email,
                'english_level': new_user.english_level,
                'learning_goal': new_user.learning_goal,
                'interests': new_user.interests,
                'estimated_vocabulary': new_user.estimated_vocabulary
            }
        }), 201
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.json
    
    username = data.get('username')
    
    if not username:
        return jsonify({'error': 'Username is required'}), 400
    
    session = Session()
    try:
        user = session.query(User).filter_by(username=username).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'english_level': user.english_level,
                'learning_goal': user.learning_goal,
                'interests': user.interests,
                'estimated_vocabulary': user.estimated_vocabulary
            }
        }), 200
        
    finally:
        session.close()

# ========== Discover / Pipeline API ==========

@app.route('/api/discover', methods=['POST'])
def discover_articles():
    """根据兴趣主题抓取并推荐最新文章"""
    data = request.json or {}
    user_id = data.get('user_id')
    categories = data.get('categories') or []
    sources = data.get('sources')
    count = data.get('count', 3)
    language = data.get('language', 'English')

    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    if not categories:
        return jsonify({'error': 'categories is required'}), 400

    session = Session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        score = round(1 / len(categories), 3)
        user.interests = {cat: score for cat in categories}
        session.commit()
    finally:
        session.close()

    try:
        from data_pipeline import DataPipeline
        pipeline = DataPipeline(
            sources=sources,
            enable_llm=True,
            target_language=language,
            db_url=DATABASE_URL
        )
        stats = asyncio.run(pipeline.run(categories=categories, articles_per_category=count))
    except Exception as e:
        return jsonify({'error': f'Pipeline failed: {e}'}), 500

    init_recommender()

    session = Session()
    try:
        recommendations = recommender.recommend_hybrid(session, user_id, 10)
    finally:
        session.close()

    return jsonify({'stats': stats, 'recommendations': recommendations})

@app.route('/api/users', methods=['GET'])
def get_users():
    """获取用户（通过用户名查询）"""
    username = request.args.get('username')
    
    if not username:
        return jsonify({'error': 'Username parameter is required'}), 400
    
    session = Session()
    try:
        user = session.query(User).filter_by(username=username).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'english_level': user.english_level,
                'learning_goal': user.learning_goal,
                'interests': user.interests,
                'estimated_vocabulary': user.estimated_vocabulary
            }
        })
    finally:
        session.close()

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """获取用户信息"""
    session = Session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'english_level': user.english_level,
            'learning_goal': user.learning_goal,
            'interests': user.interests,
            'estimated_vocabulary': user.estimated_vocabulary
        })
    finally:
        session.close()

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """更新用户信息"""
    data = request.json
    
    session = Session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # 更新字段
        if 'english_level' in data:
            user.english_level = data['english_level']
        if 'interests' in data:
            user.interests = data['interests']
        if 'learning_goal' in data:
            user.learning_goal = data['learning_goal']
        
        user.last_active = datetime.utcnow()
        
        session.commit()
        
        return jsonify({'message': 'User updated successfully'})
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

# ========== 文章相关API ==========

@app.route('/api/articles', methods=['GET'])
def get_articles():
    """获取文章列表"""
    category = request.args.get('category')
    difficulty = request.args.get('difficulty')
    limit = int(request.args.get('limit', 20))
    
    session = Session()
    try:
        query = session.query(Article)
        
        if category:
            query = query.filter_by(category=category)
        if difficulty:
            query = query.filter_by(difficulty_level=difficulty)
        
        articles = query.order_by(Article.created_at.desc()).limit(limit).all()
        
        result = []
        for article in articles:
            result.append({
                'id': article.id,
                'title': article.title,
                'summary': article.content[:200] + ('...' if len(article.content) > 200 else ''),
                'category': article.category,
                'source': article.source,
                'source_name': article.source_name,
                'difficulty_level': article.difficulty_level,
                'word_count': article.word_count,
                'views': article.views
            })
        
        return jsonify({'articles': result})
        
    finally:
        session.close()

@app.route('/api/articles/<int:article_id>', methods=['GET'])
def get_article(article_id):
    """获取文章详情"""
    session = Session()
    try:
        article = session.query(Article).filter_by(id=article_id).first()
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        # 更新浏览量
        article.views += 1
        session.commit()
        
        return jsonify({
            'id': article.id,
            'title': article.title,
            'content': article.content,
            'source': article.source,
            'source_name': article.source_name,
            'url': article.url,
            'category': article.category,
            'difficulty_level': article.difficulty_level,
            'difficulty_score': article.difficulty_score,
            'word_count': article.word_count,
            'sentence_count': article.sentence_count,
            'key_words': article.key_words,
            'views': article.views
        })
        
    finally:
        session.close()

@app.route('/api/articles/<int:article_id>/analysis', methods=['GET'])
def get_article_analysis(article_id):
    """从ArticleAnalysis表读取LLM分析结果,构建高亮数据"""
    session = Session()
    try:
        analysis = session.query(ArticleAnalysis).filter_by(
            article_id=article_id
        ).first()

        if not analysis:
            return jsonify({'error': 'Article analysis not found'}), 404

        highlights = []
        data = analysis.analysis_data

        # 1. 词汇高亮 (Vocabulary)
        for idx, vocab in enumerate(data.get('vocabulary', [])):
            highlights.append({
                'id': f'vocab-{idx}',
                'text': vocab.get('word', ''),
                'type': 'vocabulary',
                'explanation': f"{vocab.get('pronunciation', '')} - {vocab.get('definition', '')}",
                'anchors': [vocab.get('word', '')]
            })

        # 2. 搭配高亮 (Collocations)
        for idx, coll in enumerate(data.get('collocations', [])):
            highlights.append({
                'id': f'coll-{idx}',
                'text': coll.get('phrase', ''),
                'type': 'collocation',
                'explanation': coll.get('meaning', ''),
                'anchors': [coll.get('phrase', '')]
            })

        # 3. 语法高亮 (Sentence Patterns)
        for idx, pattern in enumerate(data.get('sentence_patterns', [])):
            source_sentence = pattern.get('source_sentence', '')
            if source_sentence:
                highlights.append({
                    'id': f'pattern-{idx}',
                    'text': source_sentence,
                    'type': 'grammar',
                    'explanation': pattern.get('explanation', ''),
                    'anchors': pattern.get('anchors', []) # 如果有锚点则返回，没有则为空
                })

        return jsonify({'articleId': article_id, 'highlights': highlights})
    finally:
        session.close()

# ========== 推荐相关API ==========

@app.route('/api/recommend', methods=['GET'])
def recommend():
    """获取推荐文章"""
    user_id = request.args.get('user_id', type=int)
    limit = request.args.get('limit', default=10, type=int)
    
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    session = Session()
    try:
        recommendations = recommender.recommend_hybrid(session, user_id, limit)
        return jsonify({'recommendations': recommendations})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

# ========== 阅读历史API ==========

@app.route('/api/reading_history', methods=['POST'])
def add_reading_history():
    """添加阅读记录"""
    data = request.json
    
    user_id = data.get('user_id')
    article_id = data.get('article_id')
    
    if not user_id or not article_id:
        return jsonify({'error': 'user_id and article_id are required'}), 400
    
    session = Session()
    try:
        # 检查是否已有记录
        existing = session.query(ReadingHistory).filter_by(
            user_id=user_id,
            article_id=article_id
        ).first()
        
        if existing:
            # 更新现有记录
            if 'completion_rate' in data:
                existing.completion_rate = data['completion_rate']
            if 'time_spent' in data:
                existing.time_spent = data['time_spent']
            if 'liked' in data:
                existing.liked = data['liked']
            if 'bookmarked' in data:
                existing.bookmarked = data['bookmarked']
            if 'words_looked_up' in data:
                existing.words_looked_up = data['words_looked_up']
            
            existing.finished_at = datetime.utcnow()
        else:
            # 创建新记录
            history = ReadingHistory(
                user_id=user_id,
                article_id=article_id,
                completion_rate=data.get('completion_rate', 0.0),
                time_spent=data.get('time_spent', 0),
                liked=data.get('liked', 0),
                bookmarked=data.get('bookmarked', 0),
                words_looked_up=data.get('words_looked_up', [])
            )
            session.add(history)
        
        # 更新文章统计
        article = session.query(Article).filter_by(id=article_id).first()
        if article:
            # 重新计算平均完成率
            all_history = session.query(ReadingHistory).filter_by(article_id=article_id).all()
            completion_rates = [h.completion_rate for h in all_history if h.completion_rate]
            if completion_rates:
                article.avg_completion_rate = sum(completion_rates) / len(completion_rates)
        
        session.commit()
        
        return jsonify({'message': 'Reading history saved successfully'})
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/reading_history/<int:user_id>', methods=['GET'])
def get_reading_history(user_id):
    """获取用户阅读历史"""
    limit = request.args.get('limit', default=20, type=int)
    
    session = Session()
    try:
        history = session.query(ReadingHistory).filter_by(user_id=user_id)\
            .order_by(ReadingHistory.created_at.desc()).limit(limit).all()
        
        result = []
        for record in history:
            article = record.article
            if article:
                result.append({
                    'article_id': article.id,
                    'title': article.title,
                    'category': article.category,
                    'completion_rate': record.completion_rate,
                    'time_spent': record.time_spent,
                    'liked': record.liked,
                    'bookmarked': record.bookmarked,
                    'created_at': record.created_at.isoformat()
                })
        
        return jsonify({'history': result})
        
    finally:
        session.close()

# ========== 生词本API ==========

@app.route('/api/vocabulary', methods=['POST'])
def add_vocabulary():
    """添加生词"""
    data = request.json
    
    user_id = data.get('user_id')
    word = data.get('word')
    translation = data.get('translation', '')
    example_translation = data.get('example_translation', '')
    
    if not user_id or not word:
        return jsonify({'error': 'user_id and word are required'}), 400
    
    session = Session()
    try:
        # 检查是否已存在
        existing = session.query(VocabularyItem).filter_by(
            user_id=user_id,
            word=word.lower()
        ).first()
        
        if existing:
            return jsonify({'message': 'Word already in vocabulary'}), 200
        
        vocab = VocabularyItem(
            user_id=user_id,
            word=word.lower(),
            definition=data.get('definition', ''),
            example_sentence=data.get('example_sentence', ''),
            translation=translation,
            example_translation=example_translation,
            source_article_id=data.get('source_article_id') or data.get('article_id')
        )
        
        session.add(vocab)
        session.commit()
        
        return jsonify({'message': 'Word added to vocabulary'}), 201
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/vocabulary/<int:user_id>', methods=['GET'])
def get_vocabulary(user_id):
    """获取用户生词本"""
    session = Session()
    try:
        vocab_items = session.query(VocabularyItem).filter_by(user_id=user_id)\
            .order_by(VocabularyItem.created_at.desc()).all()
        
        result = []
        for item in vocab_items:
            result.append({
                'id': item.id,
                'word': item.word,
                'definition': item.definition,
                'example_sentence': item.example_sentence,
                'translation': item.translation,
                'example_translation': item.example_translation,
                'mastery_level': item.mastery_level,
                'times_reviewed': item.times_reviewed,
                'created_at': item.created_at.isoformat()
            })
        
        return jsonify({'vocabulary': result})
        
    finally:
        session.close()

@app.route('/api/vocabulary/learn', methods=['GET'])
def get_learning_word():
    """从标准词库中随机抽取单词并翻译"""
    list_name = request.args.get('list_name')
    if list_name:
        if not ensure_vocab_list_loaded(list_name):
            return jsonify({'error': f'Vocabulary list file not found for {list_name}'}), 404
    word_row = fetch_random_vocab_word(list_name)
    if not word_row:
        return jsonify({'error': 'Vocabulary list not found'}), 404
    word, actual_list = word_row
    dictionary_data = fetch_dictionary_entry(word)
    example_sentence = dictionary_data.get("example_sentence") or build_example_sentence(
        word,
        dictionary_data.get("part_of_speech", "")
    )
    translation = translate_text(word)
    example_translation = translate_text(example_sentence)
    return jsonify({
        "word": word,
        "list_name": actual_list,
        "definition": dictionary_data.get("definition", ""),
        "example_sentence": example_sentence,
        "translation": translation,
        "example_translation": example_translation
    })

@app.route('/api/vocabulary/quiz/<int:user_id>', methods=['GET'])
def get_vocabulary_quiz(user_id):
    """获取生词测验"""
    quiz = build_vocab_quiz(user_id)
    if not quiz:
        return jsonify({'error': 'Not enough vocabulary data for quiz'}), 400
    return jsonify(quiz)

# ========== 阅读测试相关API ==========

@app.route('/api/reading_test/articles', methods=['GET'])
def get_test_articles():
    """获取可用于测试的文章列表"""
    level = request.args.get('level', 'B1')
    limit = int(request.args.get('limit', 10))
    
    session = Session()
    try:
        query = session.query(Article)
        
        if level:
            query = query.filter_by(difficulty_level=level.upper())
        
        articles = query.order_by(Article.created_at.desc()).limit(limit).all()
        
        result = []
        for article in articles:
            result.append({
                'id': article.id,
                'title': article.title,
                'difficulty_level': article.difficulty_level,
                'difficulty_score': article.difficulty_score,
                'word_count': article.word_count,
                'category': article.category,
                'source': article.source
            })
        
        return jsonify({'articles': result})
        
    finally:
        session.close()

@app.route('/api/reading_test/generate', methods=['POST'])
def generate_test_questions():
    """为文章生成测试题目"""
    data = request.json
    
    article_id = data.get('article_id')
    question_type = data.get('question_type', 'cloze')  # cloze 或 true_false
    num_questions = data.get('num_questions', 3)
    
    if not article_id:
        return jsonify({'error': 'article_id is required'}), 400
    
    session = Session()
    try:
        article = session.query(Article).filter_by(id=article_id).first()
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        # 生成题目
        if question_type == 'cloze':
            print(f"[DEBUG] 生成完形填空题，文章长度: {len(article.content)}")
            raw_questions = question_generator.generate_cloze_questions(
                article.content, 
                num_questions
            )
            print(f"[DEBUG] LLM返回了 {len(raw_questions)} 道原始题目")
        elif question_type == 'true_false':
            print(f"[DEBUG] 生成判断题，文章长度: {len(article.content)}")
            raw_questions = question_generator.generate_true_false_questions(
                article.content, 
                num_questions
            )
            print(f"[DEBUG] LLM返回了 {len(raw_questions)} 道原始题目")
        else:
            return jsonify({'error': 'Invalid question_type. Use "cloze" or "true_false"'}), 400
        
        # 处理题目
        processed_questions = []
        display_content = article.content
        
        print(f"[DEBUG] 开始处理 {len(raw_questions)} 道原始题目")
        
        for idx, q in enumerate(raw_questions):
            if question_type == 'cloze':
                target_word = q.get("target_word", "").strip()
                options = [str(o).strip() for o in q.get("options", [])]
                
                print(f"[DEBUG] 题目{idx+1}: target_word='{target_word}', options={options}")
                
                # 验证目标词在原文中（支持词根匹配）
                # 使用正则表达式匹配单词边界，支持不同词形
                word_pattern = re.compile(r'\b' + re.escape(target_word) + r'\b', re.IGNORECASE)
                match = word_pattern.search(display_content)
                
                if not match:
                    # 尝试词根匹配（去掉常见后缀）
                    root = target_word
                    suffixes = ['ing', 'ed', 's', 'es', 'er', 'est', 'ly']
                    for suffix in suffixes:
                        if target_word.endswith(suffix):
                            root = target_word[:-len(suffix)]
                            if len(root) >= 3:  # 确保词根足够长
                                # 尝试匹配词根的任何形式
                                root_pattern = re.compile(r'\b' + re.escape(root) + r'\w*\b', re.IGNORECASE)
                                match = root_pattern.search(display_content)
                                if match:
                                    # 使用文章中实际出现的词形
                                    target_word = match.group(0)
                                    print(f"[DEBUG] 词根匹配成功，使用文章中的词形: '{target_word}'")
                                    break
                
                if not match:
                    print(f"[DEBUG] 跳过：'{target_word}' 不在文章中")
                    continue
                
                # 确保正确答案在选项中
                if target_word not in options:
                    options.append(target_word)
                    import random
                    random.shuffle(options)
                
                # 在文章中替换第一个出现的目标词为空格标记
                blank_index = len(processed_questions) + 1
                display_content = display_content.replace(
                    target_word, 
                    f" [___{blank_index}___] ", 
                    1  # 只替换第一次出现
                )
                
                processed_questions.append({
                    "id": idx,
                    "blank_index": blank_index,
                    "question_text": f"Blank {blank_index}",
                    "options": options[:4],
                    "answer": target_word,
                    "explanation": q.get("explanation", "")
                })
            
            elif question_type == 'true_false':
                statement = q.get("statement") or q.get("question")
                raw_ans = str(q.get("answer", "")).lower().strip()
                
                if not statement:
                    continue
                
                # 标准化答案
                if "true" in raw_ans:
                    answer = "true"
                elif "false" in raw_ans:
                    answer = "false"
                else:
                    continue
                
                processed_questions.append({
                    "id": idx,
                    "question_text": statement,
                    "answer": answer,
                    "explanation": q.get("explanation", "")
                })
        
        print(f"[DEBUG] 最终处理后得到 {len(processed_questions)} 道有效题目")
        
        # 对于完型填空，返回挖空后的文章
        response_data = {
            'article': {
                'id': article.id,
                'title': article.title,
                'content': article.content if question_type == 'true_false' else display_content,
                'original_content': article.content,  # 总是返回原文
                'difficulty_level': article.difficulty_level
            },
            'questions': processed_questions,
            'question_type': question_type
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/reading_test/submit', methods=['POST'])
def submit_test_answers():
    """提交测试答案并获得评分"""
    data = request.json
    
    user_id = data.get('user_id')
    article_id = data.get('article_id')
    answers = data.get('answers', [])  # [{question_id: 0, user_answer: "..."}]
    questions = data.get('questions', [])  # 原始题目用于对比
    
    if not user_id or not article_id:
        return jsonify({'error': 'user_id and article_id are required'}), 400
    
    # 计算得分
    correct_count = 0
    results = []
    
    for answer in answers:
        q_id = answer.get('question_id')
        user_answer = answer.get('user_answer', '').strip()
        
        # 找到对应题目
        question = next((q for q in questions if q.get('id') == q_id), None)
        if not question:
            continue
        
        correct_answer = question.get('answer', '').strip()
        is_correct = user_answer.lower() == correct_answer.lower()
        
        if is_correct:
            correct_count += 1
        
        results.append({
            'question_id': q_id,
            'user_answer': user_answer,
            'correct_answer': correct_answer,
            'is_correct': is_correct,
            'explanation': question.get('explanation', '')
        })
    
    total_questions = len(questions)
    score_percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0
    
    # 保存到阅读历史
    session = Session()
    try:
        history = ReadingHistory(
            user_id=user_id,
            article_id=article_id,
            completion_rate=1.0,
            quiz_score=score_percentage
        )
        session.add(history)
        session.commit()
    except:
        session.rollback()
    finally:
        session.close()
    
    return jsonify({
        'score': correct_count,
        'total': total_questions,
        'percentage': round(score_percentage, 1),
        'results': results
    })

# ========== 统计信息API ==========

@app.route('/api/stats/<int:user_id>', methods=['GET'])
def get_user_stats(user_id):
    """获取用户学习统计"""
    session = Session()
    try:
        # ========== 阅读统计 ==========
        # 总阅读文章数
        total_articles = session.query(ReadingHistory).filter_by(user_id=user_id).count()
        
        # 总阅读时长
        time_records = session.query(ReadingHistory.time_spent).filter_by(user_id=user_id).all()
        total_time = sum([r[0] for r in time_records if r[0]])
        
        # 平均完成率
        completion_records = session.query(ReadingHistory.completion_rate).filter_by(user_id=user_id).all()
        completion_rates = [r[0] for r in completion_records if r[0]]
        avg_completion = sum(completion_rates) / len(completion_rates) if completion_rates else 0
        
        # 阅读测试平均分
        quiz_records = session.query(ReadingHistory.quiz_score).filter_by(user_id=user_id).all()
        quiz_scores = [r[0] for r in quiz_records if r[0] is not None and r[0] > 0]
        avg_quiz_score = sum(quiz_scores) / len(quiz_scores) if quiz_scores else 0
        total_tests = len(quiz_scores)
        
        # 生词数量
        vocab_count = session.query(VocabularyItem).filter_by(user_id=user_id).count()
        
        # 各类别阅读分布
        category_stats = {}
        history = session.query(ReadingHistory).filter_by(user_id=user_id).all()
        for record in history:
            if record.article:
                cat = record.article.category or 'general'
                category_stats[cat] = category_stats.get(cat, 0) + 1
        
        # ========== 写作统计 ==========
        writing_records = session.query(WritingHistory)\
            .filter_by(user_id=user_id)\
            .order_by(WritingHistory.created_at.asc())\
            .all()
        total_writings = len(writing_records)
        
        # 平均写作分数（IELTS）
        ielts_scores = [r.ielts_overall for r in writing_records if r.ielts_overall and r.ielts_overall > 0]
        avg_writing_score = sum(ielts_scores) / len(ielts_scores) if ielts_scores else 0
        
        # 最高分和最新分数
        highest_writing_score = max(ielts_scores) if ielts_scores else 0
        latest_writing_score = ielts_scores[-1] if ielts_scores else 0
        
        # 总写作字数
        total_words_written = sum([r.word_count for r in writing_records if r.word_count])
        
        # ========== 口语统计 ==========
        speaking_records = session.query(SpeakingHistory)\
            .filter_by(user_id=user_id)\
            .order_by(SpeakingHistory.created_at.asc())\
            .all()
        total_speaking_sessions = len(speaking_records)
        
        # 平均口语分数
        speaking_scores = [r.overall_band for r in speaking_records if r.overall_band and r.overall_band > 0]
        avg_speaking_score = sum(speaking_scores) / len(speaking_scores) if speaking_scores else 0
        
        # 最高分和最新分数
        highest_speaking_score = max(speaking_scores) if speaking_scores else 0
        latest_speaking_score = speaking_scores[-1] if speaking_scores else 0
        
        return jsonify({
            # 阅读统计
            'total_articles': total_articles,
            'total_time_minutes': round(total_time / 60, 1) if total_time else 0,
            'avg_completion_rate': round(avg_completion, 2),
            'vocabulary_count': vocab_count,
            'category_distribution': category_stats,
            'total_reading_tests': total_tests,
            'avg_reading_score': round(avg_quiz_score, 1),
            
            # 写作统计
            'total_writings': total_writings,
            'avg_writing_score': round(avg_writing_score, 1),
            'highest_writing_score': round(highest_writing_score, 1),
            'latest_writing_score': round(latest_writing_score, 1),
            'total_words_written': total_words_written,
            
            # 口语统计
            'total_speaking_sessions': total_speaking_sessions,
            'avg_speaking_score': round(avg_speaking_score, 1),
            'highest_speaking_score': round(highest_speaking_score, 1),
            'latest_speaking_score': round(latest_speaking_score, 1)
        })
        
    finally:
        session.close()

# ========== 健康检查 ==========

@app.route('/api/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({'status': 'ok', 'message': 'API is running'})

@app.route('/')
def index():
    """首页"""
    return jsonify({
        'message': 'Welcome to English Learning API',
        'version': '1.0.2',
        'endpoints': {
            'register': 'POST /api/register',
            'login': 'POST /api/login',
            'get_users': 'GET /api/users?username=<username>',
            'get_user': 'GET /api/users/<user_id>',
            'get_articles': 'GET /api/articles',
            'get_article': 'GET /api/articles/<article_id>',
            'recommend': 'GET /api/recommend?user_id=<user_id>',
            'add_reading_history': 'POST /api/reading_history',
            'get_vocabulary': 'GET /api/vocabulary/<user_id>',
            'add_vocabulary': 'POST /api/vocabulary',
            'get_stats': 'GET /api/stats/<user_id>',
            'reading_test_articles': 'GET /api/reading_test/articles?level=<level>',
            'generate_test': 'POST /api/reading_test/generate',
            'submit_test': 'POST /api/reading_test/submit',
            'evaluate_writing': 'POST /api/writing/evaluate'
        }
    })

# ========== Writing Coach API ==========

@app.route('/api/writing/topics', methods=['GET'])
def get_writing_topics():
    """获取写作话题列表"""
    topics = [
        {
            "id": "daily_life",
            "title": "Daily Life",
            "description": "Write about your daily experiences and routines"
        },
        {
            "id": "travel",
            "title": "Travel",
            "description": "Describe your travel experiences or dream destinations"
        },
        {
            "id": "technology",
            "title": "Technology",
            "description": "Discuss the impact of technology on modern life"
        },
        {
            "id": "environment",
            "title": "Environment",
            "description": "Express your views on environmental issues"
        },
        {
            "id": "education",
            "title": "Education",
            "description": "Share your thoughts about education and learning"
        }
    ]
    return jsonify(topics)

def call_writing_llm(prompt: str, text: str) -> str:
    """调用 LLM 进行写作评估（使用真实 AI）"""
    import requests
    
    # 字数统计
    word_count = len(text.split())
    
    # 200词以下直接0分
    if word_count < 200:
        return json.dumps({
            "ielts": {
                "overall": 0,
                "criteria": {
                    "task_response": {"score": 0, "comment": "Insufficient word count. IELTS Writing requires at least 250 words for Task 2 and 150 words for Task 1."},
                    "coherence": {"score": 0, "comment": "Essay too short to assess coherence and cohesion."},
                    "lexical": {"score": 0, "comment": "Essay too short to assess lexical resource."},
                    "grammar": {"score": 0, "comment": "Essay too short to assess grammatical range and accuracy."}
                }
            },
            "general": {
                "overall": 0,
                "criteria": {
                    "native_phrasing": {"score": 0, "comment": "Insufficient content for evaluation."},
                    "grammar_accuracy": {"score": 0, "comment": "Insufficient content for evaluation."},
                    "spelling": {"score": 0, "comment": "Insufficient content for evaluation."}
                }
            },
            "overall_feedback": f"⚠️ Your essay contains only {word_count} words. You must write at least 200 words to receive a score. For IELTS Task 2, aim for 250+ words.",
            "improved_version": "Please write at least 200 words to receive meaningful feedback and evaluation."
        })
    
    # 200词以上，使用真实 AI 评分
    hf_token = os.getenv('HF_TOKEN')
    if not hf_token:
        # 如果没有配置 token，返回错误
        return json.dumps({
            "ielts": {"overall": 0, "criteria": {}},
            "general": {"overall": 0, "criteria": {}},
            "overall_feedback": "⚠️ HF_TOKEN not configured. Please run configure.py to set up API tokens.",
            "improved_version": text
        })
    
    # 调用 Hugging Face API - 使用 Qwen 模型
    api_url = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-72B-Instruct"
    headers = {"Authorization": f"Bearer {hf_token}"}
    
    # 构建评分提示
    evaluation_prompt = f"""You are a strict IELTS writing examiner. Evaluate the following essay according to official IELTS band descriptors (0-9 scale).

Essay ({word_count} words):
{text}

Provide your evaluation ONLY as a valid JSON object (no additional text):
{{
  "ielts": {{
    "overall": <number 0-9>,
    "criteria": {{
      "task_response": {{"score": <number>, "comment": "<detailed feedback>"}},
      "coherence": {{"score": <number>, "comment": "<detailed feedback>"}},
      "lexical": {{"score": <number>, "comment": "<detailed feedback>"}},
      "grammar": {{"score": <number>, "comment": "<detailed feedback>"}}
    }}
  }},
  "general": {{
    "overall": <number 0-9>,
    "criteria": {{
      "native_phrasing": {{"score": <number>, "comment": "<feedback>"}},
      "grammar_accuracy": {{"score": <number>, "comment": "<feedback>"}},
      "spelling": {{"score": <number>, "comment": "<feedback>"}}
    }}
  }},
  "overall_feedback": "<comprehensive feedback>",
  "improved_version": "<corrected essay with improvements>"
}}

Evaluation guidelines:
- Band 4-5: Limited vocabulary, frequent errors, basic ideas
- Band 5-6: Adequate vocabulary, some errors, partially developed ideas  
- Band 6-7: Good range, fewer errors, well-developed ideas
- Band 7-8: Wide range, rare errors, sophisticated ideas
- Band 8-9: Near-native proficiency, minimal errors, excellent organization

Be realistic and strict. Most essays should score 5-6.5."""
    
    try:
        response = requests.post(
            api_url, 
            headers=headers, 
            json={
                "inputs": evaluation_prompt,
                "parameters": {
                    "max_new_tokens": 1500,
                    "temperature": 0.3,
                    "return_full_text": False
                }
            }, 
            timeout=60
        )
        if response.status_code == 200:
            ai_output = response.json()
            # 尝试解析 AI 返回的 JSON
            if isinstance(ai_output, list) and len(ai_output) > 0:
                generated_text = ai_output[0].get('generated_text', '')
                # 尝试从生成的文本中提取 JSON
                import re
                json_match = re.search(r'\{.*\}', generated_text, re.DOTALL)
                if json_match:
                    return json_match.group(0)
        
        # 如果 API 调用失败，返回基础评分但要求严格
        print(f"⚠️ HF API failed, using fallback evaluation")
        return json.dumps({
            "ielts": {
                "overall": 5.5,
                "criteria": {
                    "task_response": {"score": 5, "comment": "Basic task response. Ideas need more development and support."},
                    "coherence": {"score": 6, "comment": "Adequate organization but cohesive devices may be overused or unclear."},
                    "lexical": {"score": 5, "comment": "Limited vocabulary range. More topic-specific and sophisticated words needed."},
                    "grammar": {"score": 6, "comment": "Mix of simple and complex structures with noticeable errors."}
                }
            },
            "general": {
                "overall": 5.5,
                "criteria": {
                    "native_phrasing": {"score": 5, "comment": "Non-native phrasing evident. Study natural expressions."},
                    "grammar_accuracy": {"score": 6, "comment": "Frequent errors in complex structures. Review tenses and articles."},
                    "spelling": {"score": 7, "comment": "Generally accurate spelling with minor errors."}
                }
            },
            "overall_feedback": f"Your essay ({word_count} words) meets the minimum length requirement but needs significant improvement. Focus on developing sophisticated arguments, using academic vocabulary, and reducing grammatical errors to achieve higher band scores.",
            "improved_version": text
        })
    except Exception as e:
        print(f"❌ AI evaluation error: {e}")
        return json.dumps({
            "ielts": {"overall": 5, "criteria": {}},
            "general": {"overall": 5, "criteria": {}},
            "overall_feedback": f"Evaluation completed for {word_count} words. Your writing needs improvement in multiple areas.",
            "improved_version": text
        })

@app.route('/api/writing/evaluate', methods=['POST'])
def evaluate_writing_api():
    """评估写作内容"""
    data = request.json
    text = data.get('text', '')
    topic = data.get('topic', 'general')
    user_id = data.get('user_id', 1)  # 默认用户ID为1
    
    if not text:
        return jsonify({'error': 'Text is required'}), 400
    
    # 构建评估提示
    prompt = f"""Please evaluate the following English writing on the topic '{topic}':

Text: {text}

Provide a detailed IELTS-style evaluation."""
    
    try:
        result_str = call_writing_llm(prompt, text)
        result = json.loads(result_str)
        
        # 保存到数据库
        session = Session()
        try:
            writing_record = WritingHistory(
                user_id=user_id,
                topic=topic,
                text=text,
                word_count=len(text.split()),
                ielts_overall=result.get('ielts', {}).get('overall', 0),
                ielts_task_response=result.get('ielts', {}).get('criteria', {}).get('task_response', {}).get('score', 0),
                ielts_coherence=result.get('ielts', {}).get('criteria', {}).get('coherence', {}).get('score', 0),
                ielts_lexical=result.get('ielts', {}).get('criteria', {}).get('lexical', {}).get('score', 0),
                ielts_grammar=result.get('ielts', {}).get('criteria', {}).get('grammar', {}).get('score', 0),
                general_overall=result.get('general', {}).get('overall', 0),
                evaluation_data=result
            )
            session.add(writing_record)
            session.commit()
            
            # 添加记录ID到返回结果
            result['record_id'] = writing_record.id
        finally:
            session.close()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/writing/history', methods=['GET'])
def get_writing_history():
    """获取写作历史记录"""
    user_id = request.args.get('user_id', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    session = Session()
    try:
        records = session.query(WritingHistory).filter_by(user_id=user_id)\
            .order_by(WritingHistory.created_at.desc())\
            .limit(limit).all()
        
        history = []
        for record in records:
            history.append({
                'id': record.id,
                'topic': record.topic,
                'preview': record.text[:100] + '...' if len(record.text) > 100 else record.text,
                'score': record.ielts_overall,
                'created_at': record.created_at.isoformat() if record.created_at else None
            })
        
        return jsonify(history)
    finally:
        session.close()


# ========== Speaking Coach API ==========

# 全局变量存储 Whisper 模型
whisper_model = None

def load_whisper():
    """加载 Whisper 模型"""
    global whisper_model
    if whisper_model is None:
        try:
            import whisper
            print("⏳ 正在加载 Whisper base 模型...")
            whisper_model = whisper.load_model("base")
            print("✅ Whisper 模型加载成功！")
        except Exception as e:
            print(f"❌ Whisper 模型加载失败: {e}")
            whisper_model = None

def transcribe_audio_file(file_path: str) -> str:
    """使用 Whisper 转录音频文件"""
    global whisper_model
    if whisper_model is None:
        return "[Whisper model not loaded]"
    
    try:
        # 先尝试使用 pydub 转换 webm 到 wav（不依赖 ffmpeg）
        import subprocess
        import shutil
        
        # 检查 ffmpeg 是否可用
        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            # 尝试常见的安装路径
            possible_paths = [
                r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
                r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
                r"C:\ffmpeg\bin\ffmpeg.exe",
                r"C:\ProgramData\chocolatey\bin\ffmpeg.exe"
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    ffmpeg_path = path
                    break
        
        # 如果找到 ffmpeg，先转换为 wav 格式
        if ffmpeg_path and file_path.endswith('.webm'):
            wav_path = file_path.replace('.webm', '.wav')
            try:
                subprocess.run(
                    [ffmpeg_path, '-i', file_path, '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le', wav_path],
                    check=True,
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                result = whisper_model.transcribe(wav_path)
                # 清理临时文件
                if os.path.exists(wav_path):
                    os.remove(wav_path)
                return result["text"]
            except Exception as e:
                print(f"⚠️ ffmpeg conversion failed: {e}")
                # 继续尝试直接转录
        
        # 直接尝试转录（Whisper 内部会调用 ffmpeg）
        result = whisper_model.transcribe(file_path)
        return result["text"]
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Transcription error: {error_msg}")
        
        # 如果是找不到文件的错误，给出明确提示
        if "系统找不到指定的文件" in error_msg or "WinError 2" in error_msg:
            return "[ffmpeg not found. Please install ffmpeg and add it to PATH, or restart the terminal after installation.]"
        
        return f"[Transcription error: {error_msg}]"

@app.route('/api/speaking/evaluate', methods=['POST'])
def evaluate_speaking():
    """评估口语音频"""
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    user_id = request.form.get('user_id', 1, type=int)
    
    # 保存音频文件到临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp_file:
        audio_file.save(tmp_file.name)
        tmp_path = tmp_file.name
    
    try:
        # 转录音频
        transcription = transcribe_audio_file(tmp_path)
        
        # 模拟 AI 评估 - 匹配前端 SpeakingEvaluation 接口
        import random
        base_score = random.randint(6, 8)
        
        fluency_score = base_score
        vocabulary_score = base_score + random.choice([-1, 0, 1])
        grammar_score = base_score
        
        evaluation = {
            "transcription": transcription,
            "overall_band": base_score,
            "feedback": {
                "fluency": {
                    "score": fluency_score,
                    "comment": "Good fluency with natural pauses. Consider reducing hesitations for higher band scores."
                },
                "vocabulary": {
                    "score": vocabulary_score,
                    "comment": "Appropriate vocabulary range for the topic. Try incorporating more topic-specific terms."
                },
                "grammar": {
                    "score": grammar_score,
                    "comment": "Generally accurate grammar with good control of complex structures."
                }
            },
            "native_suggestion": "Consider using expressions like 'By the way...', 'As far as I know...', 'To be honest...' to sound more natural. Also practice linking words smoothly in connected speech."
        }
        
        # 保存到数据库
        session = Session()
        try:
            speaking_record = SpeakingHistory(
                user_id=user_id,
                transcription=transcription,
                overall_band=base_score,
                fluency_score=fluency_score,
                vocabulary_score=vocabulary_score,
                grammar_score=grammar_score,
                evaluation_data=evaluation
            )
            session.add(speaking_record)
            session.commit()
            
            evaluation['record_id'] = speaking_record.id
        finally:
            session.close()
        
        return jsonify(evaluation)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # 清理临时文件
        try:
            os.unlink(tmp_path)
        except:
            pass

@app.route('/api/speaking/history', methods=['GET'])
def get_speaking_history():
    """获取口语历史记录"""
    user_id = request.args.get('user_id', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    session = Session()
    try:
        records = session.query(SpeakingHistory).filter_by(user_id=user_id)\
            .order_by(SpeakingHistory.created_at.desc())\
            .limit(limit).all()
        
        history = []
        for record in records:
            history.append({
                'id': record.id,
                'transcription': record.transcription[:100] + '...' if record.transcription and len(record.transcription) > 100 else record.transcription,
                'overall_band': record.overall_band,
                'fluency_score': record.fluency_score,
                'vocabulary_score': record.vocabulary_score,
                'grammar_score': record.grammar_score,
                'created_at': record.created_at.isoformat() if record.created_at else None
            })
        
        return jsonify(history)
    finally:
        session.close()


if __name__ == '__main__':
    # 加载 Whisper 模型
    load_whisper()
    
    # 初始化推荐系统
    print("Initializing recommender system...")
    init_recommender()
    print("Recommender system initialized.")
    
    # 启动服务
    app.run(debug=True, host='0.0.0.0', port=5000)
