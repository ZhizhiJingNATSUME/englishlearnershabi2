"""
文本分析器
功能：文本统计、难度评估（CEFR）
不含 Embedding 生成（后续集成）
"""
import re
import logging
from typing import Dict, Tuple, List
from collections import Counter

import nltk
import textstat

logger = logging.getLogger(__name__)

# 确保 NLTK 数据
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt_tab', quiet=True)


class TextAnalyzer:
    """文本分析器 - CEFR 难度评估"""

    def __init__(self):
        try:
            self.stop_words = set(nltk.corpus.stopwords.words('english'))
        except Exception:
            nltk.download('stopwords', quiet=True)
            self.stop_words = set(nltk.corpus.stopwords.words('english'))

    def analyze(self, content: str) -> Dict:
        """
        分析文本内容

        Args:
            content: 纯文本内容

        Returns:
            分析结果字典
        """
        if not content or len(content) < 50:
            return self._empty_result()

        # 1. 文本统计
        stats = self._compute_stats(content)

        # 2. 难度评估
        level, score = self._estimate_difficulty(
            stats['flesch_score'],
            stats['avg_sentence_length'],
            stats['rare_word_ratio']
        )

        # 3. 提取关键词
        key_words = self._extract_keywords(content)

        return {
            'difficulty_level': level,
            'difficulty_score': score,
            'word_count': stats['word_count'],
            'sentence_count': stats['sentence_count'],
            'avg_sentence_length': stats['avg_sentence_length'],
            'unique_words': stats['unique_words'],
            'key_words': key_words
        }

    def _compute_stats(self, text: str) -> Dict:
        """计算文本统计"""
        # 分词
        words = nltk.word_tokenize(text.lower())
        words = [w for w in words if w.isalpha()]

        # 句子分割
        sentences = nltk.sent_tokenize(text)

        # 统计
        word_count = len(words)
        sentence_count = len(sentences)
        avg_sentence_length = word_count / max(sentence_count, 1)
        unique_words = len(set(words))

        # 稀有词比例（非停用词且长度>5）
        rare_words = [w for w in words if w not in self.stop_words and len(w) > 5]
        rare_word_ratio = len(rare_words) / max(word_count, 1)

        # Flesch 可读性分数
        flesch_score = textstat.flesch_reading_ease(text)

        return {
            'word_count': word_count,
            'sentence_count': sentence_count,
            'avg_sentence_length': round(avg_sentence_length, 2),
            'unique_words': unique_words,
            'rare_word_ratio': rare_word_ratio,
            'flesch_score': flesch_score
        }

    def _estimate_difficulty(
        self,
        flesch_score: float,
        avg_sentence_length: float,
        rare_word_ratio: float
    ) -> Tuple[str, float]:
        """
        估算 CEFR 难度等级

        Returns:
            (level, score) - 如 ('B1', 45.5)
        """
        # Flesch 分数贡献（反向 - 分数越低越难）
        if flesch_score >= 90:
            flesch_contribution = 0
        elif flesch_score >= 80:
            flesch_contribution = 15
        elif flesch_score >= 70:
            flesch_contribution = 30
        elif flesch_score >= 60:
            flesch_contribution = 45
        elif flesch_score >= 50:
            flesch_contribution = 60
        elif flesch_score >= 30:
            flesch_contribution = 75
        else:
            flesch_contribution = 90

        # 句长贡献
        if avg_sentence_length < 10:
            length_contribution = 10
        elif avg_sentence_length < 15:
            length_contribution = 30
        elif avg_sentence_length < 20:
            length_contribution = 50
        elif avg_sentence_length < 25:
            length_contribution = 70
        else:
            length_contribution = 90

        # 综合评分
        difficulty_score = (
            flesch_contribution * 0.4 +
            length_contribution * 0.3 +
            rare_word_ratio * 100 * 0.3
        )

        difficulty_score = max(0, min(100, difficulty_score))

        # CEFR 映射
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

    def _extract_keywords(self, text: str, max_keywords: int = 20) -> List[str]:
        """提取关键词（频率>=2的非停用词）"""
        words = nltk.word_tokenize(text.lower())
        words = [w for w in words if w.isalpha() and w not in self.stop_words and len(w) > 3]

        word_freq = Counter(words)
        keywords = [word for word, freq in word_freq.most_common(max_keywords * 2) if freq >= 2]

        return keywords[:max_keywords]

    def _empty_result(self) -> Dict:
        """返回空结果"""
        return {
            'difficulty_level': 'B1',
            'difficulty_score': 50.0,
            'word_count': 0,
            'sentence_count': 0,
            'avg_sentence_length': 0.0,
            'unique_words': 0,
            'key_words': []
        }
