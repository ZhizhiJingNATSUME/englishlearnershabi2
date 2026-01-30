"""
Smart Article Recommendation System
基于用户行为的智能文章推荐系统

Features:
- Content-based filtering using embeddings (FAISS)
- User behavior signals (likes, dislikes, reading history)
- Difficulty level matching
- Interest-based ranking
- Popularity & engagement signals
- Cold-start handling for new users
"""
import json
import logging
import numpy as np
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
from datetime import datetime, timedelta
import faiss

logger = logging.getLogger(__name__)


class ArticleRecommender:
    """
    智能文章推荐器
    
    Combines multiple signals for ranking:
    1. Content similarity (embedding-based)
    2. User level matching (CEFR difficulty)
    3. Interest alignment (category preferences)
    4. Engagement signals (completion rate, likes)
    5. Freshness (recency bonus)
    """
    
    # CEFR等级映射
    LEVEL_MAP = {'A1': 1, 'A2': 2, 'B1': 3, 'B2': 4, 'C1': 5, 'C2': 6}
    REVERSE_LEVEL_MAP = {v: k for k, v in LEVEL_MAP.items()}
    
    # 推荐权重配置
    WEIGHTS = {
        'content_similarity': 0.35,  # 内容相似度
        'level_fit': 0.25,           # 难度匹配
        'interest_match': 0.20,      # 兴趣匹配
        'engagement': 0.10,          # 参与度信号
        'freshness': 0.10            # 新鲜度
    }
    
    def __init__(self):
        """初始化推荐器"""
        self.index = None
        self.article_ids = []
        self.article_metadata = {}
        self.embedding_dim = None
        
        # 类别embedding缓存
        self._category_embeddings = {}
    
    def build_index(self, articles: List[Dict]):
        """
        构建向量索引
        
        Args:
            articles: 文章列表，每个包含 id, title, category, 
                     difficulty_level, embedding, views, avg_completion_rate 等
        """
        if not articles:
            logger.warning("No articles to index")
            return
        
        embeddings = []
        self.article_ids = []
        self.article_metadata = {}
        
        for article in articles:
            try:
                embedding = article.get('embedding')
                if not embedding:
                    continue
                
                # 解析 embedding
                if isinstance(embedding, str):
                    embedding = json.loads(embedding)
                
                if not embedding or len(embedding) < 10:
                    continue
                
                embeddings.append(embedding)
                article_id = article['id']
                self.article_ids.append(article_id)
                
                # 存储元数据用于排序
                self.article_metadata[article_id] = {
                    'title': article.get('title', ''),
                    'category': (article.get('category') or 'general').lower(),
                    'difficulty_level': article.get('difficulty_level', 'B1'),
                    'difficulty_score': article.get('difficulty_score', 50),
                    'views': article.get('views', 0),
                    'avg_completion_rate': article.get('avg_completion_rate', 0.0),
                    'created_at': article.get('created_at'),
                    'embedding': embedding  # 存储用于相似度计算
                }
                
            except Exception as e:
                logger.error(f"Error processing article {article.get('id', 'unknown')}: {e}")
                continue
        
        if not embeddings:
            logger.warning("No valid embeddings found in articles")
            return
        
        # 转换为 numpy 数组
        embeddings_array = np.array(embeddings, dtype=np.float32)
        self.embedding_dim = embeddings_array.shape[1]
        
        # 归一化（用于余弦相似度）
        faiss.normalize_L2(embeddings_array)
        
        # 创建 FAISS 索引 (Inner Product = cosine similarity after normalization)
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        self.index.add(embeddings_array)
        
        logger.info(f"Built index with {len(self.article_ids)} articles "
                   f"(embedding dim: {self.embedding_dim})")
    
    def get_user_profile(self, session, user_id: int) -> Optional[Dict]:
        """
        获取用户画像
        
        Returns:
            dict with:
            - user_id, english_level, learning_goal
            - interests: {category: weight}
            - user_embedding: List[float] or None
            - liked_articles: Set[int]
            - disliked_articles: Set[int]
            - read_articles: Set[int]
            - category_preferences: {category: {reads, likes, avg_completion}}
        """
        from models import User, ReadingHistory, Article
        
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            logger.warning(f"User {user_id} not found")
            return None
        
        # 获取阅读历史
        history = session.query(ReadingHistory).filter_by(user_id=user_id)\
            .order_by(ReadingHistory.created_at.desc()).all()
        
        # 分析历史数据
        liked_articles = set()
        disliked_articles = set()
        read_articles = set()
        liked_embeddings = []
        disliked_embeddings = []
        category_stats = defaultdict(lambda: {
            'reads': 0, 
            'likes': 0, 
            'dislikes': 0,
            'total_completion': 0.0,
            'total_time': 0
        })
        
        for record in history:
            article = record.article
            if not article:
                continue
            
            read_articles.add(article.id)
            cat = (article.category or 'general').lower()
            category_stats[cat]['reads'] += 1
            
            if record.completion_rate:
                category_stats[cat]['total_completion'] += record.completion_rate
            if record.time_spent:
                category_stats[cat]['total_time'] += record.time_spent
            
            # 处理喜欢/不喜欢
            if record.liked == 1:
                liked_articles.add(article.id)
                category_stats[cat]['likes'] += 1
                
                # 收集喜欢的文章的embedding
                if article.embedding:
                    try:
                        emb = json.loads(article.embedding) if isinstance(article.embedding, str) else article.embedding
                        liked_embeddings.append(emb)
                    except:
                        pass
                        
            elif record.liked == -1:
                disliked_articles.add(article.id)
                category_stats[cat]['dislikes'] += 1
                
                # 收集不喜欢的文章的embedding
                if article.embedding:
                    try:
                        emb = json.loads(article.embedding) if isinstance(article.embedding, str) else article.embedding
                        disliked_embeddings.append(emb)
                    except:
                        pass
        
        # 计算用户embedding
        user_embedding = self._compute_user_embedding(
            liked_embeddings, 
            disliked_embeddings,
            user.user_embedding
        )
        
        # 计算兴趣权重
        interests = self._compute_interest_weights(category_stats, user.interests)
        
        # 计算类别偏好详情
        category_preferences = {}
        for cat, stats in category_stats.items():
            if stats['reads'] > 0:
                category_preferences[cat] = {
                    'reads': stats['reads'],
                    'likes': stats['likes'],
                    'dislikes': stats['dislikes'],
                    'avg_completion': stats['total_completion'] / stats['reads'],
                    'engagement_score': self._compute_engagement_score(stats)
                }
        
        return {
            'user_id': user_id,
            'english_level': user.english_level or 'B1',
            'learning_goal': user.learning_goal or 'general',
            'interests': interests,
            'user_embedding': user_embedding,
            'liked_articles': liked_articles,
            'disliked_articles': disliked_articles,
            'read_articles': read_articles,
            'category_preferences': category_preferences,
            'estimated_vocabulary': user.estimated_vocabulary or 0
        }
    
    def _compute_user_embedding(
        self, 
        liked_embeddings: List[List[float]], 
        disliked_embeddings: List[List[float]],
        stored_embedding: str = None
    ) -> Optional[List[float]]:
        """
        计算用户embedding
        结合喜欢的文章和不喜欢的文章
        """
        # 如果没有足够的行为数据，使用存储的embedding
        if len(liked_embeddings) < 3 and stored_embedding:
            try:
                return json.loads(stored_embedding)
            except:
                pass
        
        if not liked_embeddings:
            return None
        
        try:
            # 对喜欢的文章计算加权平均（最近的权重更高）
            liked_array = np.array(liked_embeddings[-20:])  # 最多使用最近20篇
            n = len(liked_array)
            
            # 时间衰减权重
            recency_weights = np.exp(np.linspace(-1, 0, n))
            recency_weights = recency_weights / recency_weights.sum()
            
            user_embedding = np.average(liked_array, axis=0, weights=recency_weights)
            
            # 减去不喜欢的文章的影响
            if disliked_embeddings:
                disliked_array = np.array(disliked_embeddings[-10:])
                disliked_avg = np.mean(disliked_array, axis=0)
                # 轻微减去不喜欢的方向
                user_embedding = user_embedding - 0.2 * disliked_avg
            
            # 归一化
            norm = np.linalg.norm(user_embedding)
            if norm > 0:
                user_embedding = user_embedding / norm
            
            return user_embedding.tolist()
            
        except Exception as e:
            logger.error(f"Error computing user embedding: {e}")
            return None
    
    def _compute_interest_weights(
        self, 
        category_stats: Dict, 
        stored_interests: Dict = None
    ) -> Dict[str, float]:
        """
        计算用户对各类别的兴趣权重
        """
        if not category_stats:
            return stored_interests or {}
        
        total_reads = sum(stats['reads'] for stats in category_stats.values())
        if total_reads == 0:
            return stored_interests or {}
        
        interests = {}
        for cat, stats in category_stats.items():
            # 综合考虑：阅读量、喜欢比例、完成率
            read_ratio = stats['reads'] / total_reads
            
            like_ratio = stats['likes'] / max(stats['reads'], 1)
            dislike_ratio = stats['dislikes'] / max(stats['reads'], 1)
            completion_ratio = stats['total_completion'] / max(stats['reads'], 1)
            
            # 加权计算兴趣分数
            interest_score = (
                read_ratio * 0.3 +
                like_ratio * 0.4 +
                completion_ratio * 0.3 -
                dislike_ratio * 0.3  # 惩罚不喜欢
            )
            
            interests[cat] = max(0, round(interest_score, 3))
        
        # 归一化
        total = sum(interests.values())
        if total > 0:
            interests = {k: round(v/total, 3) for k, v in interests.items()}
        
        return interests
    
    def _compute_engagement_score(self, stats: Dict) -> float:
        """计算类别的参与度分数"""
        if stats['reads'] == 0:
            return 0.0
        
        like_rate = stats['likes'] / stats['reads']
        dislike_rate = stats['dislikes'] / stats['reads']
        avg_completion = stats['total_completion'] / stats['reads']
        
        score = like_rate * 0.4 + avg_completion * 0.4 - dislike_rate * 0.2
        return max(0, min(1, score))
    
    def recommend_cold_start(
        self, 
        session, 
        user_id: int, 
        limit: int = 10,
        excluded_ids: Set[int] = None
    ) -> List[Dict]:
        """
        冷启动推荐（新用户或数据不足）
        
        Strategy:
        1. 根据用户设置的兴趣和水平筛选
        2. 按热度（完成率+浏览量）排序
        3. 多样化：每个类别最多2篇
        """
        from models import User, Article
        
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return []
        
        excluded_ids = excluded_ids or set()
        
        # 获取用户水平和兴趣
        user_level = user.english_level or 'B1'
        interests = user.interests or {}
        
        # 确定可接受的难度范围
        user_level_num = self.LEVEL_MAP.get(user_level, 3)
        acceptable_levels = []
        for offset in [-1, 0, 1]:
            level = self.REVERSE_LEVEL_MAP.get(user_level_num + offset)
            if level:
                acceptable_levels.append(level)
        
        # 查询候选文章
        query = session.query(Article)\
            .filter(Article.difficulty_level.in_(acceptable_levels))\
            .filter(~Article.id.in_(excluded_ids) if excluded_ids else True)
        
        # 如果有兴趣偏好，优先相关类别
        preferred_categories = []
        if interests:
            preferred_categories = sorted(
                interests.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            preferred_categories = [cat for cat, score in preferred_categories if score > 0.1]
        
        # 获取候选文章
        candidates = query.order_by(
            Article.avg_completion_rate.desc(),
            Article.views.desc()
        ).limit(limit * 3).all()
        
        # 多样化选择
        result = []
        category_counts = defaultdict(int)
        max_per_category = 2
        
        # 优先选择偏好类别
        for article in candidates:
            cat = (article.category or 'general').lower()
            
            # 检查类别配额
            if category_counts[cat] >= max_per_category:
                continue
            
            # 偏好类别加分
            is_preferred = cat in preferred_categories
            
            # Calculate simple scores for cold start
            interest_score = interests.get(cat, 0.0) if interests else 0.0
            level_match = 1.0 if article.difficulty_level == user_level else 0.7
            
            result.append({
                'id': article.id,
                'title': article.title,
                'content': article.content or '',  # Send full content - let frontend truncate
                'category': article.category,
                'source': article.source,
                'source_name': article.source_name,
                'difficulty_level': article.difficulty_level,
                'word_count': article.word_count,
                'score': 0.5 + (0.2 if is_preferred else 0),
                'reason': 'Popular in your level' + (' & matches your interests' if is_preferred else ''),
                'detailed_scores': {
                    'content_similarity': 0.5,  # Not applicable for cold start
                    'level_fit': level_match,
                    'interest_match': interest_score,
                    'engagement': min((article.views or 0) / 100.0, 1.0),
                    'freshness': 0.8
                }
            })
            
            category_counts[cat] += 1
            
            if len(result) >= limit:
                break
        
        return result
    
    def recommend_content_based(
        self,
        user_profile: Dict,
        excluded_ids: Set[int],
        limit: int = 10
    ) -> List[Tuple[int, float, str, Dict]]:
        """
        基于内容的推荐
        
        Returns:
            List of (article_id, score, reason, detailed_scores)
        """
        if self.index is None:
            logger.warning("Index not built, cannot do content-based recommendation")
            return []
        
        user_embedding = user_profile.get('user_embedding')
        if not user_embedding:
            logger.info("No user embedding, skipping content-based recommendation")
            return []
        
        user_level = user_profile.get('english_level', 'B1')
        user_level_num = self.LEVEL_MAP.get(user_level, 3)
        interests = user_profile.get('interests', {})
        
        # 使用 FAISS 搜索相似文章
        query_embedding = np.array([user_embedding], dtype=np.float32)
        faiss.normalize_L2(query_embedding)
        
        # 搜索足够多的候选（后续过滤）
        k = min(200, len(self.article_ids))
        distances, indices = self.index.search(query_embedding, k)
        
        recommendations = []
        
        for idx, similarity in zip(indices[0], distances[0]):
            if idx < 0 or idx >= len(self.article_ids):
                continue
            
            article_id = self.article_ids[idx]
            
            # 排除已读/已排除
            if article_id in excluded_ids:
                continue
            
            metadata = self.article_metadata.get(article_id, {})
            
            # 计算各项得分
            scores = self._compute_article_scores(
                metadata, 
                float(similarity),
                user_level_num,
                interests
            )
            
            # 如果难度差距太大，跳过
            if scores['level_penalty'] > 0.5:
                continue
            
            # 计算最终加权分数
            final_score = (
                scores['content_similarity'] * self.WEIGHTS['content_similarity'] +
                scores['level_fit'] * self.WEIGHTS['level_fit'] +
                scores['interest_match'] * self.WEIGHTS['interest_match'] +
                scores['engagement'] * self.WEIGHTS['engagement'] +
                scores['freshness'] * self.WEIGHTS['freshness']
            )
            
            # 生成推荐理由
            reason = self._generate_recommendation_reason(scores, metadata)
            
            # Extract detailed scores (remove level_penalty as it's internal)
            detailed_scores = {
                'content_similarity': scores['content_similarity'],
                'level_fit': scores['level_fit'],
                'interest_match': scores['interest_match'],
                'engagement': scores['engagement'],
                'freshness': scores['freshness']
            }
            
            recommendations.append((article_id, final_score, reason, detailed_scores))
            
            if len(recommendations) >= limit * 2:  # 多取一些用于后续多样化
                break
        
        # 按分数排序
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        return recommendations[:limit]
    
    def _compute_article_scores(
        self,
        metadata: Dict,
        similarity: float,
        user_level_num: int,
        interests: Dict[str, float]
    ) -> Dict[str, float]:
        """
        计算文章各维度的得分
        """
        # 1. 内容相似度 (已归一化到 [0, 1])
        content_score = max(0, min(1, (similarity + 1) / 2))  # [-1,1] -> [0,1]
        
        # 2. 难度匹配度
        article_level = metadata.get('difficulty_level', 'B1')
        article_level_num = self.LEVEL_MAP.get(article_level, 3)
        level_diff = abs(article_level_num - user_level_num)
        
        # 偏难一点比偏简单好（学习目的）
        if article_level_num > user_level_num:
            level_diff *= 0.8  # 稍难的惩罚小一些
        
        level_score = max(0, 1 - level_diff * 0.3)
        level_penalty = level_diff * 0.25
        
        # 3. 兴趣匹配度
        category = metadata.get('category', 'general').lower()
        interest_score = interests.get(category, 0.1)  # 默认给一点分
        
        # 4. 参与度信号
        completion_rate = metadata.get('avg_completion_rate', 0)
        views = metadata.get('views', 0)
        
        engagement_score = (
            min(1, completion_rate) * 0.7 +
            min(1, views / 100) * 0.3  # 浏览量归一化
        )
        
        # 5. 新鲜度
        created_at = metadata.get('created_at')
        if created_at:
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except:
                    created_at = None
            
            if created_at:
                days_old = (datetime.now() - created_at.replace(tzinfo=None)).days
                freshness_score = max(0, 1 - days_old / 30)  # 30天内线性衰减
            else:
                freshness_score = 0.5
        else:
            freshness_score = 0.5
        
        return {
            'content_similarity': content_score,
            'level_fit': level_score,
            'level_penalty': level_penalty,
            'interest_match': interest_score,
            'engagement': engagement_score,
            'freshness': freshness_score
        }
    
    def _generate_recommendation_reason(self, scores: Dict, metadata: Dict) -> str:
        """生成推荐理由"""
        reasons = []
        
        if scores['content_similarity'] > 0.7:
            reasons.append("Similar to articles you liked")
        
        if scores['level_fit'] > 0.8:
            reasons.append("Perfect difficulty for your level")
        elif scores['level_fit'] > 0.6:
            reasons.append("Good challenge for improvement")
        
        if scores['interest_match'] > 0.3:
            reasons.append(f"Matches your interest in {metadata.get('category', 'this topic')}")
        
        if scores['engagement'] > 0.7:
            reasons.append("Highly rated by other learners")
        
        if scores['freshness'] > 0.8:
            reasons.append("Fresh content")
        
        if not reasons:
            reasons.append("Recommended for you")
        
        return " • ".join(reasons[:2])
    
    def recommend_hybrid(
        self, 
        session, 
        user_id: int, 
        limit: int = 10
    ) -> List[Dict]:
        """
        混合推荐策略
        
        Combines:
        1. Content-based filtering (embeddings)
        2. Collaborative signals (engagement data)
        3. Cold-start fallback
        """
        from models import Article
        
        # 获取用户画像
        user_profile = self.get_user_profile(session, user_id)
        if not user_profile:
            return []
        
        # 已读文章集合
        excluded_ids = (
            user_profile['read_articles'] | 
            user_profile['disliked_articles']
        )
        
        # 判断是否是新用户（少于5篇阅读历史且没有用户embedding）
        is_new_user = (
            len(user_profile['read_articles']) < 5 or 
            user_profile['user_embedding'] is None
        )
        
        recommendations = []
        
        if not is_new_user and self.index is not None:
            # 基于内容的推荐
            content_recs = self.recommend_content_based(
                user_profile,
                excluded_ids,
                limit
            )
            
            for article_id, score, reason, detailed_scores in content_recs:
                recommendations.append({
                    'article_id': article_id,
                    'score': score,
                    'reason': reason,
                    'detailed_scores': detailed_scores,
                    'source': 'content_based'
                })
        
        # 如果推荐不足，用冷启动补充
        if len(recommendations) < limit:
            remaining = limit - len(recommendations)
            existing_ids = {r['article_id'] for r in recommendations}
            
            cold_start_recs = self.recommend_cold_start(
                session,
                user_id,
                remaining,
                excluded_ids | existing_ids
            )
            
            for rec in cold_start_recs:
                recommendations.append({
                    'article_id': rec['id'],
                    'score': rec.get('score', 0.5),
                    'reason': rec.get('reason', 'Popular article'),
                    'source': 'cold_start',
                    # 直接传递完整信息避免重复查询
                    '_article_data': rec
                })
        
        # 获取完整文章信息
        article_ids = [r['article_id'] for r in recommendations if '_article_data' not in r]
        
        if article_ids:
            articles = session.query(Article).filter(Article.id.in_(article_ids)).all()
            article_map = {a.id: a for a in articles}
        else:
            article_map = {}
        
        # 构建最终结果
        result = []
        seen_ids = set()
        
        for rec in recommendations:
            article_id = rec['article_id']
            
            if article_id in seen_ids:
                continue
            seen_ids.add(article_id)
            
            # 优先使用预加载的数据
            if '_article_data' in rec:
                data = rec['_article_data']
                result.append({
                    'id': data['id'],
                    'title': data['title'],
                    'content': data.get('content', ''),  # Send full content - let frontend truncate
                    'category': data['category'],
                    'source': data.get('source'),
                    'source_name': data.get('source_name'),
                    'difficulty_level': data['difficulty_level'],
                    'word_count': data.get('word_count'),
                    'recommendation_score': rec['score'],
                    'recommendation_reason': rec['reason'],
                    'recommendation_reasons': rec.get('detailed_scores', {})
                })
            elif article_id in article_map:
                article = article_map[article_id]
                result.append({
                    'id': article.id,
                    'title': article.title,
                    'content': article.content or '',  # Send full content - let frontend truncate
                    'category': article.category,
                    'source': article.source,
                    'source_name': article.source_name,
                    'difficulty_level': article.difficulty_level,
                    'word_count': article.word_count,
                    'recommendation_score': rec['score'],
                    'recommendation_reason': rec['reason'],
                    'recommendation_reasons': rec.get('detailed_scores', {})
                })
            
            if len(result) >= limit:
                break
        
        # 按分数排序返回
        result.sort(key=lambda x: x.get('recommendation_score', 0), reverse=True)
        
        return result
    
    def update_user_embedding(self, session, user_id: int) -> bool:
        """
        更新用户embedding（在用户交互后调用）
        
        Returns:
            True if updated successfully
        """
        from models import User
        
        user_profile = self.get_user_profile(session, user_id)
        
        if not user_profile:
            logger.warning(f"User {user_id} not found")
            return False
        
        if not user_profile.get('user_embedding'):
            liked_count = len(user_profile.get('liked_articles', set()))
            logger.info(f"User {user_id} has no embedding (liked articles: {liked_count}, need at least 1 with embedding)")
            return False
        
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                user.user_embedding = json.dumps(user_profile['user_embedding'])
                user.interests = user_profile.get('interests', {})
                session.commit()
                
                liked_count = len(user_profile.get('liked_articles', set()))
                disliked_count = len(user_profile.get('disliked_articles', set()))
                logger.info(f"✓ Updated embedding for user {user_id} "
                           f"(liked: {liked_count}, disliked: {disliked_count}, "
                           f"interests: {list(user_profile['interests'].keys())})")
                return True
        except Exception as e:
            logger.error(f"Error updating user embedding: {e}")
            session.rollback()
        
        return False
    
    def get_similar_articles(
        self,
        session,
        article_id: int,
        limit: int = 5,
        excluded_ids: Set[int] = None
    ) -> List[Dict]:
        """
        获取相似文章（用于"更多类似文章"功能）
        """
        from models import Article
        
        if self.index is None:
            return []
        
        # 获取文章embedding
        metadata = self.article_metadata.get(article_id)
        if not metadata or 'embedding' not in metadata:
            # 从数据库获取
            article = session.query(Article).filter_by(id=article_id).first()
            if not article or not article.embedding:
                return []
            
            try:
                embedding = json.loads(article.embedding)
            except:
                return []
        else:
            embedding = metadata['embedding']
        
        excluded_ids = excluded_ids or set()
        excluded_ids.add(article_id)
        
        # FAISS 搜索
        query = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(query)
        
        k = min(50, len(self.article_ids))
        distances, indices = self.index.search(query, k)
        
        result = []
        for idx, sim in zip(indices[0], distances[0]):
            if idx < 0 or idx >= len(self.article_ids):
                continue
            
            aid = self.article_ids[idx]
            if aid in excluded_ids:
                continue
            
            meta = self.article_metadata.get(aid, {})
            result.append({
                'id': aid,
                'title': meta.get('title', ''),
                'category': meta.get('category', ''),
                'difficulty_level': meta.get('difficulty_level', ''),
                'similarity_score': float(sim)
            })
            
            if len(result) >= limit:
                break
        
        return result


# 单例实例（可选）
_recommender_instance = None

def get_recommender() -> ArticleRecommender:
    """获取推荐器单例"""
    global _recommender_instance
    if _recommender_instance is None:
        _recommender_instance = ArticleRecommender()
    return _recommender_instance
