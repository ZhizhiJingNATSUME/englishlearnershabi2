"""
内容处理模块：抓取、清洗、分析文章
"""
import re
import json
import nltk
import textstat
import numpy as np
from typing import Dict, List, Tuple
from collections import Counter
from sentence_transformers import SentenceTransformer
import wikipedia

# 下载必要的NLTK数据
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

class ContentProcessor:
    """内容处理器"""
    
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        """初始化处理器"""
        self.model = SentenceTransformer(model_name)
        self.stop_words = set(stopwords.words('english'))
        
        # 常用词频列表（简化版，实际应该从词频数据库加载）
        self.common_words = self._load_common_words()
    
    def _load_common_words(self) -> set:
        """加载常用词列表（前2000个高频词）"""
        # 这里使用简化版本，实际应该加载完整的词频表
        common = set([
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
            'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
            'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
            'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what',
            # ... 实际应该包含2000个词
        ])
        return common
    
    def get_specific_topics(self) -> Dict[str, List[str]]:
        """获取每个类别下的具体主题"""
        return {
            'Technology': [
                'Artificial intelligence',
                'Machine learning',
                'Cloud computing',
                'Blockchain',
                'Internet of Things',
                'Cybersecurity',
                'Virtual reality',
                'Quantum computing',
                '5G technology',
                'Robotics'
            ],
            'Science': [
                'Climate change',
                'DNA',
                'Evolution',
                'Black hole',
                'Photosynthesis',
                'Renewable energy',
                'Vaccine',
                'Genetics',
                'Ecosystem',
                'Astronomy'
            ],
            'History': [
                'World War II',
                'Ancient Egypt',
                'Roman Empire',
                'Industrial Revolution',
                'Renaissance',
                'Cold War',
                'American Revolution',
                'French Revolution',
                'Ancient Greece',
                'Middle Ages'
            ],
            'Geography': [
                'Amazon rainforest',
                'Sahara Desert',
                'Mount Everest',
                'Great Barrier Reef',
                'Antarctica',
                'Pacific Ocean',
                'Mediterranean Sea',
                'Himalayas',
                'Grand Canyon',
                'Nile River'
            ],
            'Health': [
                'Nutrition',
                'Exercise',
                'Mental health',
                'Sleep',
                'Stress management',
                'Immune system',
                'Heart disease',
                'Diabetes',
                'Cancer research',
                'Public health'
            ],
            'Sports': [
                'Olympic Games',
                'Football World Cup',
                'Basketball',
                'Tennis',
                'Swimming',
                'Marathon',
                'Athletics',
                'Baseball',
                'Golf',
                'Cricket'
            ],
            'Arts': [
                'Renaissance art',
                'Impressionism',
                'Pablo Picasso',
                'Leonardo da Vinci',
                'Vincent van Gogh',
                'Modern art',
                'Abstract art',
                'Sculpture',
                'Photography',
                'Digital art'
            ],
            'Music': [
                'Classical music',
                'Jazz',
                'Rock music',
                'Pop music',
                'Hip hop',
                'Opera',
                'Blues',
                'Electronic music',
                'Musical instruments',
                'Music theory'
            ],
            'Literature': [
                'William Shakespeare',
                'Poetry',
                'Novel',
                'Jane Austen',
                'Charles Dickens',
                'Ernest Hemingway',
                'Contemporary literature',
                'Science fiction',
                'Fantasy literature',
                'Drama'
            ],
            'Business': [
                'Entrepreneurship',
                'Marketing',
                'Stock market',
                'E-commerce',
                'Supply chain',
                'Corporate finance',
                'Business strategy',
                'Human resources',
                'International trade',
                'Economics'
            ]
        }
    
    def fetch_wikipedia_articles(self, topics: List[str], count_per_topic: int = 5) -> List[Dict]:
        """从维基百科抓取文章 - 改进版本，抓取具体主题"""
        articles = []
        specific_topics = self.get_specific_topics()
        
        for category in topics:
            # 获取该类别下的具体主题
            subtopics = specific_topics.get(category, [category])
            
            # 随机选择一些子主题（避免太多）
            import random
            selected_subtopics = random.sample(subtopics, min(count_per_topic, len(subtopics)))
            
            print(f"\nFetching articles for category '{category}':")
            print(f"  Selected subtopics: {', '.join(selected_subtopics)}")
            
            for subtopic in selected_subtopics:
                try:
                    # 直接获取这个具体主题的文章
                    page = wikipedia.page(subtopic, auto_suggest=True)
                    
                    # 过滤太短的文章
                    if len(page.content) < 500:
                        print(f"  ✗ '{page.title}' - Too short, skipped")
                        continue
                    
                    article = {
                        'title': page.title,
                        'content': page.content,
                        'url': page.url,
                        'source': 'wikipedia',
                        'category': category  # 使用主类别，不是子主题
                    }
                    
                    articles.append(article)
                    print(f"  ✓ '{page.title}' - Fetched successfully")
                    
                except wikipedia.exceptions.DisambiguationError as e:
                    # 如果有歧义，选择第一个选项
                    try:
                        page = wikipedia.page(e.options[0], auto_suggest=False)
                        if len(page.content) >= 500:
                            article = {
                                'title': page.title,
                                'content': page.content,
                                'url': page.url,
                                'source': 'wikipedia',
                                'category': category
                            }
                            articles.append(article)
                            print(f"  ✓ '{page.title}' - Fetched (disambiguation resolved)")
                    except Exception as inner_e:
                        print(f"  ✗ '{subtopic}' - Error: {inner_e}")
                        continue
                        
                except Exception as e:
                    print(f"  ✗ '{subtopic}' - Error: {e}")
                    continue
        
        return articles
    
    def clean_text(self, text: str) -> str:
        """清洗文本"""
        # 移除多余的空白
        text = re.sub(r'\s+', ' ', text)
        
        # 移除特殊字符但保留基本标点
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\'\"]', '', text)
        
        # 移除维基百科的引用标记
        text = re.sub(r'\[\d+\]', '', text)
        
        return text.strip()
    
    def split_into_paragraphs(self, text: str, max_words: int = 300) -> List[str]:
        """将长文本分割成适合阅读的段落"""
        paragraphs = text.split('\n')
        result = []
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            words = para.split()
            if len(words) <= max_words:
                result.append(para)
            else:
                # 按句子分割
                sentences = sent_tokenize(para)
                current = []
                current_length = 0
                
                for sent in sentences:
                    sent_words = len(sent.split())
                    if current_length + sent_words <= max_words:
                        current.append(sent)
                        current_length += sent_words
                    else:
                        if current:
                            result.append(' '.join(current))
                        current = [sent]
                        current_length = sent_words
                
                if current:
                    result.append(' '.join(current))
        
        return result
    
    def analyze_text(self, text: str) -> Dict:
        """分析文本特征"""
        # 分词
        words = word_tokenize(text.lower())
        words = [w for w in words if w.isalpha()]
        
        sentences = sent_tokenize(text)
        
        # 基本统计
        word_count = len(words)
        sentence_count = len(sentences)
        avg_sentence_length = word_count / max(sentence_count, 1)
        unique_words = len(set(words))
        
        # 词汇难度分析
        non_common_words = [w for w in words if w not in self.common_words and w not in self.stop_words]
        rare_word_ratio = len(non_common_words) / max(word_count, 1)
        
        # 可读性分数
        flesch_score = textstat.flesch_reading_ease(text)
        
        # 识别关键生词（频率低但重要的词）
        word_freq = Counter(non_common_words)
        key_words = [word for word, count in word_freq.most_common(15) if count >= 2]
        
        return {
            'word_count': word_count,
            'sentence_count': sentence_count,
            'avg_sentence_length': avg_sentence_length,
            'unique_words': unique_words,
            'rare_word_ratio': rare_word_ratio,
            'flesch_score': flesch_score,
            'key_words': key_words
        }
    
    def estimate_difficulty(self, analysis: Dict) -> Tuple[str, float]:
        """估算文章难度等级"""
        # 基于多个指标综合评估
        flesch = analysis['flesch_score']
        avg_sent_len = analysis['avg_sentence_length']
        rare_ratio = analysis['rare_word_ratio']
        
        # 计算综合难度分数 (0-100)
        # Flesch分数越高越简单，我们反转它
        difficulty_score = 0
        
        # Flesch贡献 (40%)
        if flesch >= 80:
            difficulty_score += 10
        elif flesch >= 60:
            difficulty_score += 25
        elif flesch >= 50:
            difficulty_score += 40
        elif flesch >= 30:
            difficulty_score += 60
        else:
            difficulty_score += 80
        
        difficulty_score *= 0.4
        
        # 句子长度贡献 (30%)
        if avg_sent_len <= 10:
            difficulty_score += 10 * 0.3
        elif avg_sent_len <= 15:
            difficulty_score += 30 * 0.3
        elif avg_sent_len <= 20:
            difficulty_score += 50 * 0.3
        elif avg_sent_len <= 25:
            difficulty_score += 70 * 0.3
        else:
            difficulty_score += 90 * 0.3
        
        # 生词比例贡献 (30%)
        difficulty_score += rare_ratio * 100 * 0.3
        
        # 映射到CEFR等级
        if difficulty_score < 20:
            level = 'A1'
        elif difficulty_score < 35:
            level = 'A2'
        elif difficulty_score < 50:
            level = 'B1'
        elif difficulty_score < 65:
            level = 'B2'
        elif difficulty_score < 80:
            level = 'C1'
        else:
            level = 'C2'
        
        return level, round(difficulty_score, 2)
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """生成文本向量"""
        # 使用句子截断避免太长
        text_truncated = text[:512]  # 限制长度
        embedding = self.model.encode(text_truncated)
        return embedding
    
    def process_article(self, article: Dict) -> Dict:
        """处理单篇文章"""
        # 清洗文本
        cleaned_content = self.clean_text(article['content'])
        
        # 如果文章太长，取前面的部分
        paragraphs = self.split_into_paragraphs(cleaned_content, max_words=400)
        if paragraphs:
            # 使用第一个段落或组合前几个段落
            content_to_use = paragraphs[0]
            if len(content_to_use.split()) < 150 and len(paragraphs) > 1:
                content_to_use = ' '.join(paragraphs[:2])
        else:
            content_to_use = cleaned_content[:2000]
        
        # 分析文本
        analysis = self.analyze_text(content_to_use)
        
        # 估算难度
        difficulty_level, difficulty_score = self.estimate_difficulty(analysis)
        
        # 生成向量
        embedding = self.generate_embedding(content_to_use)
        
        # 组装结果
        processed = {
            'title': article['title'],
            'content': content_to_use,
            'source': article.get('source', 'unknown'),
            'url': article.get('url', ''),
            'category': article.get('category', 'general'),
            'difficulty_level': difficulty_level,
            'difficulty_score': difficulty_score,
            'word_count': analysis['word_count'],
            'sentence_count': analysis['sentence_count'],
            'avg_sentence_length': analysis['avg_sentence_length'],
            'unique_words': analysis['unique_words'],
            'key_words': analysis['key_words'],
            'embedding': embedding.tolist()  # 转换为列表以便JSON序列化
        }
        
        return processed
    
    def batch_process_articles(self, articles: List[Dict]) -> List[Dict]:
        """批量处理文章"""
        processed = []
        
        for i, article in enumerate(articles):
            try:
                print(f"Processing article {i+1}/{len(articles)}: {article.get('title', 'Unknown')}")
                result = self.process_article(article)
                processed.append(result)
            except Exception as e:
                print(f"Error processing article: {e}")
                continue
        
        return processed

