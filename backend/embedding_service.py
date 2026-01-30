"""
Embedding Service - 生成文章和用户的语义向量
使用 sentence-transformers 模型生成高质量embeddings
"""
import os
import json
import logging
import numpy as np
from typing import List, Dict, Optional, Union
from functools import lru_cache

logger = logging.getLogger(__name__)

# 全局模型实例（懒加载）
_model = None
_model_name = None


def get_embedding_model(model_name: str = "all-MiniLM-L6-v2"):
    """
    获取或加载 sentence-transformers 模型
    
    Args:
        model_name: 模型名称，支持:
            - "all-MiniLM-L6-v2" (默认，384维，快速)
            - "all-mpnet-base-v2" (768维，更准确)
            - "paraphrase-multilingual-MiniLM-L12-v2" (多语言支持)
    """
    global _model, _model_name
    
    if _model is None or _model_name != model_name:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {model_name}")
            _model = SentenceTransformer(model_name)
            _model_name = model_name
            logger.info(f"Model loaded successfully. Embedding dimension: {_model.get_sentence_embedding_dimension()}")
        except ImportError:
            logger.error("sentence-transformers not installed. Run: pip install sentence-transformers")
            raise
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    return _model


def generate_text_embedding(
    text: str,
    model_name: str = "all-MiniLM-L6-v2"
) -> Optional[List[float]]:
    """
    为单个文本生成 embedding
    
    Args:
        text: 输入文本
        model_name: 模型名称
    
    Returns:
        embedding 向量 (list of floats) 或 None
    """
    if not text or len(text.strip()) < 10:
        logger.warning("Text too short for embedding")
        return None
    
    try:
        model = get_embedding_model(model_name)
        
        # 截取前8000字符（约2000词）以避免过长输入
        text_truncated = text[:8000]
        
        # 生成 embedding
        embedding = model.encode(text_truncated, convert_to_numpy=True)
        
        # 归一化
        embedding = embedding / np.linalg.norm(embedding)
        
        return embedding.tolist()
    
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return None


def generate_batch_embeddings(
    texts: List[str],
    model_name: str = "all-MiniLM-L6-v2",
    batch_size: int = 32
) -> List[Optional[List[float]]]:
    """
    批量生成 embeddings
    
    Args:
        texts: 文本列表
        model_name: 模型名称
        batch_size: 批处理大小
    
    Returns:
        embedding 列表
    """
    if not texts:
        return []
    
    try:
        model = get_embedding_model(model_name)
        
        # 预处理：截断过长文本
        processed_texts = []
        valid_indices = []
        
        for i, text in enumerate(texts):
            if text and len(text.strip()) >= 10:
                processed_texts.append(text[:8000])
                valid_indices.append(i)
        
        if not processed_texts:
            return [None] * len(texts)
        
        # 批量编码
        embeddings = model.encode(
            processed_texts,
            convert_to_numpy=True,
            batch_size=batch_size,
            show_progress_bar=len(processed_texts) > 10
        )
        
        # 归一化
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / norms
        
        # 填充结果
        results = [None] * len(texts)
        for idx, valid_idx in enumerate(valid_indices):
            results[valid_idx] = embeddings[idx].tolist()
        
        return results
    
    except Exception as e:
        logger.error(f"Error generating batch embeddings: {e}")
        return [None] * len(texts)


def generate_article_embedding(
    title: str,
    content: str,
    category: str = "",
    key_words: List[str] = None,
    model_name: str = "all-MiniLM-L6-v2"
) -> Optional[List[float]]:
    """
    为文章生成 embedding
    结合标题、内容、类别、关键词生成综合向量
    
    Args:
        title: 文章标题
        content: 文章内容
        category: 文章类别
        key_words: 关键词列表
        model_name: 模型名称
    
    Returns:
        embedding 向量
    """
    # 构建复合文本（标题权重更高）
    parts = [
        f"Title: {title}",
        f"Category: {category}" if category else "",
        f"Keywords: {', '.join(key_words[:10])}" if key_words else "",
        f"Content: {content[:6000]}"  # 内容截断
    ]
    
    combined_text = "\n".join(p for p in parts if p)
    
    return generate_text_embedding(combined_text, model_name)


def generate_user_embedding(
    liked_embeddings: List[List[float]],
    disliked_embeddings: List[List[float]] = None,
    interest_weights: Dict[str, float] = None,
    category_embeddings: Dict[str, List[float]] = None
) -> Optional[List[float]]:
    """
    根据用户行为生成用户 embedding
    
    Args:
        liked_embeddings: 用户喜欢的文章 embeddings
        disliked_embeddings: 用户不喜欢的文章 embeddings
        interest_weights: 用户兴趣权重 {"technology": 0.4, ...}
        category_embeddings: 类别对应的 embeddings（可选）
    
    Returns:
        用户 embedding 向量
    """
    if not liked_embeddings:
        return None
    
    try:
        # 计算喜欢的文章的加权平均
        liked_array = np.array(liked_embeddings)
        
        # 最近的文章权重更高（时间衰减）
        n = len(liked_array)
        recency_weights = np.exp(np.linspace(-1, 0, n))  # 指数衰减
        recency_weights = recency_weights / recency_weights.sum()
        
        user_embedding = np.average(liked_array, axis=0, weights=recency_weights)
        
        # 减去不喜欢的文章的影响（如果有）
        if disliked_embeddings:
            disliked_array = np.array(disliked_embeddings)
            disliked_avg = np.mean(disliked_array, axis=0)
            
            # 轻微减去不喜欢的方向
            user_embedding = user_embedding - 0.3 * disliked_avg
        
        # 如果有兴趣权重和类别embeddings，可以进一步调整
        if interest_weights and category_embeddings:
            interest_vector = np.zeros_like(user_embedding)
            total_weight = 0
            
            for cat, weight in interest_weights.items():
                if cat in category_embeddings:
                    interest_vector += weight * np.array(category_embeddings[cat])
                    total_weight += weight
            
            if total_weight > 0:
                interest_vector /= total_weight
                # 混合行为embedding和兴趣embedding
                user_embedding = 0.7 * user_embedding + 0.3 * interest_vector
        
        # 归一化
        user_embedding = user_embedding / np.linalg.norm(user_embedding)
        
        return user_embedding.tolist()
    
    except Exception as e:
        logger.error(f"Error generating user embedding: {e}")
        return None


def compute_similarity(
    embedding1: List[float],
    embedding2: List[float]
) -> float:
    """
    计算两个embedding的余弦相似度
    
    Args:
        embedding1: 第一个向量
        embedding2: 第二个向量
    
    Returns:
        相似度分数 [-1, 1]
    """
    if not embedding1 or not embedding2:
        return 0.0
    
    try:
        v1 = np.array(embedding1)
        v2 = np.array(embedding2)
        
        # 假设已归一化，直接点积
        similarity = np.dot(v1, v2)
        
        return float(similarity)
    
    except Exception as e:
        logger.error(f"Error computing similarity: {e}")
        return 0.0


def get_embedding_dimension(model_name: str = "all-MiniLM-L6-v2") -> int:
    """获取 embedding 维度"""
    model = get_embedding_model(model_name)
    return model.get_sentence_embedding_dimension()


# 预定义的类别 embeddings（懒加载）
_category_embeddings = {}

# 统一的类别定义（所有数据源共用，全部小写）
# Sources: NewsAPI, VOA, Wikipedia
UNIFIED_CATEGORIES = {
    "technology": "Technology news about computers, software, AI, gadgets, smartphones, robotics, and digital innovation",
    "science": "Scientific discoveries, research, physics, biology, chemistry, astronomy, mathematics, and academic findings",
    "health": "Health and medical news about diseases, treatments, wellness, nutrition, fitness, mental health, and healthcare",
    "business": "Business news about economy, finance, stock markets, companies, startups, entrepreneurship, and trade",
    "education": "Education news about schools, universities, learning methods, teachers, language learning, and academic policies",
    "culture": "Culture and arts news about traditions, art history, museums, literature, music, philosophy, and cultural events",
    "sports": "Sports news about games, athletes, tournaments, football, basketball, olympics, and athletic competitions",
    "entertainment": "Entertainment news about movies, TV shows, music, celebrities, video games, theater, and pop culture",
    
    # General fallback
    "general": "General news and current events covering various topics from around the world"
}

def get_category_embedding(category: str) -> List[float]:
    """
    获取预定义类别的 embedding
    用于增强推荐的类别匹配
    """
    global _category_embeddings
    
    if not _category_embeddings:
        # 为所有统一类别生成 embeddings
        for cat, description in UNIFIED_CATEGORIES.items():
            embedding = generate_text_embedding(description)
            if embedding:
                _category_embeddings[cat] = embedding
    
    # 始终使用小写进行查找
    normalized_category = category.lower() if category else "general"
    return _category_embeddings.get(normalized_category, _category_embeddings.get("general"))


def get_all_categories() -> List[str]:
    """获取所有支持的类别列表"""
    return list(UNIFIED_CATEGORIES.keys())


if __name__ == "__main__":
    # 测试
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Embedding Service...")
    
    # 测试单个文本
    text = "Artificial Intelligence is transforming the technology industry with new innovations."
    embedding = generate_text_embedding(text)
    print(f"Single embedding shape: {len(embedding) if embedding else None}")
    
    # 测试文章 embedding
    article_emb = generate_article_embedding(
        title="AI Revolution in Healthcare",
        content="Machine learning algorithms are being used to diagnose diseases faster and more accurately than ever before.",
        category="technology",
        key_words=["AI", "healthcare", "machine learning", "diagnosis"]
    )
    print(f"Article embedding shape: {len(article_emb) if article_emb else None}")
    
    # 测试批量
    texts = [
        "The stock market showed significant gains today.",
        "Scientists discovered a new species in the Amazon rainforest.",
        "The new smartphone features improved battery life."
    ]
    batch_embs = generate_batch_embeddings(texts)
    print(f"Batch embeddings: {len([e for e in batch_embs if e])} valid out of {len(batch_embs)}")
    
    # 测试相似度
    sim = compute_similarity(embedding, article_emb)
    print(f"Similarity between texts: {sim:.4f}")
    
    print("Embedding Service test completed!")

