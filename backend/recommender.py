"""
推荐系统模块
"""
import json
import numpy as np
from typing import List, Dict, Tuple
from collections import defaultdict
import faiss

class ArticleRecommender:
    """文章推荐器"""
    
    def __init__(self):
        """初始化推荐器"""
        self.index = None
        self.article_ids = []
        self.article_metadata = {}
        
        # CEFR等级映射到数值
        self.level_map = {
            'A1': 1, 'A2': 2, 'B1': 3, 'B2': 4, 'C1': 5, 'C2': 6
        }
        self.reverse_level_map = {v: k for k, v in self.level_map.items()}
    
    def build_index(self, articles: List[Dict]):
        """构建向量索引"""
        if not articles:
            print("No articles to index")
            return
        
        # 提取embeddings
        embeddings = []
        self.article_ids = []
        self.article_metadata = {}
        
        for article in articles:
            try:
                if 'embedding' in article and article['embedding']:
                    embedding = article['embedding']
                    if isinstance(embedding, str):
                        embedding = json.loads(embedding)
                    
                    embeddings.append(embedding)
                    article_id = article['id']
                    self.article_ids.append(article_id)
                    
                    # 存储元数据
                    self.article_metadata[article_id] = {
                        'title': article['title'],
                        'category': article.get('category', 'general'),
                        'difficulty_level': article.get('difficulty_level', 'B1'),
                        'difficulty_score': article.get('difficulty_score', 50),
                        'views': article.get('views', 0),
                        'avg_completion_rate': article.get('avg_completion_rate', 0.0)
                    }
            except Exception as e:
                print(f"Error processing article {article.get('id', 'unknown')}: {e}")
                continue
        
        if not embeddings:
            print("No valid embeddings found")
            return
        
        # 转换为numpy数组
        embeddings_array = np.array(embeddings, dtype=np.float32)
        
        # 归一化
        faiss.normalize_L2(embeddings_array)
        
        # 创建FAISS索引
        dimension = embeddings_array.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner Product (cosine similarity after normalization)
        self.index.add(embeddings_array)
        
        print(f"Built index with {len(self.article_ids)} articles")
    
    def get_user_profile(self, session, user_id: int) -> Dict:
        """获取用户画像"""
        from models import User, ReadingHistory
        
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return None
        
        # 用户兴趣
        interests = user.interests if user.interests else {}
        
        # 用户embedding (从喜欢的文章计算)
        user_embedding = None
        if user.user_embedding:
            try:
                user_embedding = json.loads(user.user_embedding)
            except:
                pass
        
        # 如果没有预计算的embedding，从历史记录计算
        if user_embedding is None:
            liked_history = session.query(ReadingHistory).filter(
                ReadingHistory.user_id == user_id,
                ReadingHistory.liked == 1
            ).all()
            
            if liked_history:
                liked_embeddings = []
                for history in liked_history:
                    article = history.article
                    if article and article.embedding:
                        try:
                            emb = json.loads(article.embedding) if isinstance(article.embedding, str) else article.embedding
                            liked_embeddings.append(emb)
                        except:
                            continue
                
                if liked_embeddings:
                    user_embedding = np.mean(liked_embeddings, axis=0).tolist()
        
        # 分析阅读历史，更新兴趣分布
        history = session.query(ReadingHistory).filter_by(user_id=user_id).all()
        
        category_stats = defaultdict(lambda: {'count': 0, 'total_completion': 0, 'likes': 0})
        
        for record in history:
            article = record.article
            if article:
                cat = article.category or 'general'
                category_stats[cat]['count'] += 1
                if record.completion_rate:
                    category_stats[cat]['total_completion'] += record.completion_rate
                if record.liked == 1:
                    category_stats[cat]['likes'] += 1
        
        # 计算兴趣分数
        if category_stats:
            total_interactions = sum(stats['count'] for stats in category_stats.values())
            new_interests = {}
            
            for cat, stats in category_stats.items():
                # 综合考虑：阅读次数、完成率、点赞数
                score = (
                    stats['count'] / total_interactions * 0.4 +
                    (stats['total_completion'] / max(stats['count'], 1)) * 0.3 +
                    (stats['likes'] / max(stats['count'], 1)) * 0.3
                )
                new_interests[cat] = round(score, 3)
            
            # 更新用户兴趣
            if new_interests:
                interests = new_interests
        
        return {
            'user_id': user_id,
            'english_level': user.english_level or 'B1',
            'learning_goal': user.learning_goal or 'general',
            'interests': interests,
            'user_embedding': user_embedding,
            'estimated_vocabulary': user.estimated_vocabulary or 0
        }
    
    def recommend_cold_start(self, session, user_id: int, limit: int = 10) -> List[int]:
        """冷启动推荐（新用户）"""
        from models import User, Article
        
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return []
        
        # 获取用户设置的兴趣和水平
        interests = user.interests if user.interests else {}
        user_level = user.english_level or 'B1'
        
        # 查询符合条件的文章
        query = session.query(Article)
        
        # 过滤难度：用户水平±1级
        user_level_num = self.level_map.get(user_level, 3)
        acceptable_levels = [
            self.reverse_level_map.get(user_level_num - 1),
            self.reverse_level_map.get(user_level_num),
            self.reverse_level_map.get(user_level_num + 1)
        ]
        acceptable_levels = [l for l in acceptable_levels if l]
        
        query = query.filter(Article.difficulty_level.in_(acceptable_levels))
        
        # 如果用户有兴趣偏好，优先推荐相关类别
        if interests:
            preferred_categories = sorted(interests.items(), key=lambda x: x[1], reverse=True)
            preferred_categories = [cat for cat, score in preferred_categories if score > 0.1]
            
            if preferred_categories:
                # 尝试先只筛选偏好列别的
                query_filtered = query.filter(Article.category.in_(preferred_categories))
                if query_filtered.count() > 0:
                     query = query_filtered
        
        # 按热度排序（views和完成率）
        articles = query.order_by(
            Article.avg_completion_rate.desc(),
            Article.views.desc()
        ).limit(limit).all()
        
        return [article.id for article in articles]
    
    def recommend_content_based(self, user_embedding: List[float], user_level: str, 
                                excluded_ids: List[int], limit: int = 10) -> List[Tuple[int, float]]:
        """基于内容的推荐"""
        if self.index is None or user_embedding is None:
            return []
        
        # 转换为numpy数组并归一化
        query_embedding = np.array([user_embedding], dtype=np.float32)
        faiss.normalize_L2(query_embedding)
        
        # 搜索相似文章（搜索更多候选，后续过滤）
        k = min(100, len(self.article_ids))
        distances, indices = self.index.search(query_embedding, k)
        
        # 过滤和排序
        user_level_num = self.level_map.get(user_level, 3)
        
        recommendations = []
        for idx, distance in zip(indices[0], distances[0]):
            article_id = self.article_ids[idx]
            
            # 排除已读文章
            if article_id in excluded_ids:
                continue
            
            metadata = self.article_metadata.get(article_id, {})
            
            # 难度匹配度
            article_level = metadata.get('difficulty_level', 'B1')
            article_level_num = self.level_map.get(article_level, 3)
            level_diff = abs(article_level_num - user_level_num)
            
            # 难度差距太大，跳过
            if level_diff > 2:
                continue
            
            # 计算综合分数
            similarity_score = float(distance)
            level_fit_score = 1.0 - (level_diff * 0.2)
            popularity_score = min(metadata.get('avg_completion_rate', 0) + 0.1, 1.0)
            
            final_score = (
                similarity_score * 0.6 +
                level_fit_score * 0.3 +
                popularity_score * 0.1
            )
            
            recommendations.append((article_id, final_score))
            
            if len(recommendations) >= limit:
                break
        
        # 按分数排序
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        return recommendations[:limit]
    
    def recommend_hybrid(self, session, user_id: int, limit: int = 10) -> List[Dict]:
        """混合推荐策略"""
        from models import ReadingHistory, Article
        
        # 获取用户画像
        user_profile = self.get_user_profile(session, user_id)
        if not user_profile:
            return []
        
        # 获取用户已读文章ID
        read_articles = session.query(ReadingHistory.article_id).filter_by(user_id=user_id).all()
        excluded_ids = set([r[0] for r in read_articles])
        
        # 判断是否是新用户（读过的文章少于5篇）
        is_new_user = len(excluded_ids) < 5
        
        recommended_ids = []
        
        if is_new_user:
            # 冷启动推荐
            recommended_ids = self.recommend_cold_start(session, user_id, limit)
        else:
            # 基于内容的推荐
            if user_profile.get('user_embedding'):
                content_recs = self.recommend_content_based(
                    user_profile['user_embedding'],
                    user_profile['english_level'],
                    list(excluded_ids),
                    limit
                )
                recommended_ids = [article_id for article_id, score in content_recs]
            
            # 如果推荐不足，用冷启动补充
            if len(recommended_ids) < limit:
                cold_start_recs = self.recommend_cold_start(session, user_id, limit - len(recommended_ids))
                for rec_id in cold_start_recs:
                    if rec_id not in recommended_ids and rec_id not in excluded_ids:
                        recommended_ids.append(rec_id)
        
        # 获取文章详情
        if not recommended_ids:
            return []
        
        articles = session.query(Article).filter(Article.id.in_(recommended_ids)).all()
        
        # 保持推荐顺序
        article_map = {article.id: article for article in articles}
        result = []
        
        for article_id in recommended_ids:
            if article_id in article_map:
                article = article_map[article_id]
                result.append({
                    'id': article.id,
                    'title': article.title,
                    'content': article.content[:200] + '...',  # 预览
                    'category': article.category,
                    'source': article.source,
                    'source_name': article.source_name,
                    'difficulty_level': article.difficulty_level,
                    'word_count': article.word_count
                })
        
        return result

