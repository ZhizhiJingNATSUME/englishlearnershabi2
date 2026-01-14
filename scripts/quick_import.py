"""
快速导入测试文章
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models import init_db, get_session, Article
from datetime import datetime

# 测试文章数据
SAMPLE_ARTICLES = [
    {
        "title": "Climate Change: A Global Challenge",
        "content": """Climate change is one of the most pressing issues facing our planet today. Rising global temperatures are causing ice caps to melt, sea levels to rise, and weather patterns to become more extreme. Scientists agree that human activities, particularly the burning of fossil fuels, are the primary cause of this warming trend.

The effects of climate change are already being felt around the world. Coastal cities are experiencing increased flooding, while agricultural regions are suffering from prolonged droughts. Many species of plants and animals are struggling to adapt to changing environmental conditions.

To address this challenge, countries must work together to reduce greenhouse gas emissions. This includes transitioning to renewable energy sources like solar and wind power, improving energy efficiency, and protecting forests that absorb carbon dioxide. Individual actions, such as reducing consumption and choosing sustainable products, also play an important role.

While the challenge is significant, there is still time to make a difference. By taking action now, we can help ensure a livable planet for future generations.""",
        "source": "wikipedia",
        "source_name": "Wikipedia",
        "url": "https://en.wikipedia.org/wiki/Climate_change",
        "difficulty_level": "B2",
        "difficulty_score": 7.2,
        "word_count": 176,
        "key_vocabulary": ["climate change", "greenhouse gas", "renewable energy", "fossil fuels", "emissions"],
        "topics": ["environment", "science", "global warming"]
    },
    {
        "title": "The Benefits of Daily Exercise",
        "content": """Regular exercise is essential for maintaining good health. It helps strengthen your heart, improves blood circulation, and boosts your immune system. Even just 30 minutes of moderate activity each day can make a big difference.

Exercise doesn't have to be difficult or expensive. Simple activities like walking, cycling, or dancing can be very effective. The key is to find something you enjoy and make it part of your daily routine.

Beyond physical health, exercise also improves mental well-being. It reduces stress, helps you sleep better, and increases your energy levels throughout the day. Many people find that regular exercise improves their mood and helps them feel more positive.

Starting a new exercise routine can be challenging, but it's important to start slowly and gradually increase your activity level. Setting realistic goals and tracking your progress can help you stay motivated.""",
        "source": "wikipedia",
        "source_name": "Wikipedia",
        "url": "https://en.wikipedia.org/wiki/Exercise",
        "difficulty_level": "A2",
        "difficulty_score": 4.5,
        "word_count": 148,
        "key_vocabulary": ["exercise", "health", "routine", "circulation", "immune system"],
        "topics": ["health", "fitness", "lifestyle"]
    },
    {
        "title": "The History of the Internet",
        "content": """The Internet has transformed how we communicate, work, and live. Its origins can be traced back to the 1960s when the U.S. Department of Defense developed ARPANET, a network designed to share information between computers at different locations.

In the 1980s, the development of TCP/IP protocols allowed different computer networks to communicate with each other. This laid the foundation for what would become the global Internet. The invention of the World Wide Web by Tim Berners-Lee in 1989 made the Internet accessible to ordinary people.

The 1990s saw explosive growth in Internet usage. Email became a common form of communication, and websites began to offer information, entertainment, and commercial services. Search engines like Google made it easy to find information online.

Today, the Internet is an integral part of modern life. It enables instant communication across the globe, provides access to vast amounts of information, and supports countless businesses and services. Mobile devices have made it possible to stay connected anywhere, at any time.

As technology continues to evolve, the Internet will undoubtedly play an even more important role in shaping our future.""",
        "source": "wikipedia",
        "source_name": "Wikipedia",
        "url": "https://en.wikipedia.org/wiki/Internet",
        "difficulty_level": "B1",
        "difficulty_score": 6.0,
        "word_count": 198,
        "key_vocabulary": ["Internet", "network", "protocol", "World Wide Web", "communication"],
        "topics": ["technology", "history", "communication"]
    },
    {
        "title": "Understanding Quantum Mechanics",
        "content": """Quantum mechanics represents one of the most profound and counterintuitive theories in modern physics. At its core, it describes the behavior of matter and energy at the atomic and subatomic scales, where classical physics breaks down and peculiar phenomena emerge.

The foundational principle of quantum mechanics is wave-particle duality, which posits that particles can exhibit both wave-like and particle-like properties depending on how they are observed. This was famously demonstrated in the double-slit experiment, where electrons create an interference pattern characteristic of waves when not observed, but behave like discrete particles when measured.

Another cornerstone concept is Heisenberg's uncertainty principle, which states that certain pairs of physical properties, such as position and momentum, cannot be simultaneously known with arbitrary precision. This fundamental limitation is not due to measurement inadequacies but represents an intrinsic feature of quantum systems.

Quantum entanglement, perhaps the most mysterious aspect of quantum mechanics, occurs when particles become correlated in such a way that the quantum state of one particle cannot be described independently of the others, regardless of the spatial separation between them. Einstein famously referred to this phenomenon as "spooky action at a distance."

The implications of quantum mechanics extend far beyond theoretical physics. Modern technologies such as semiconductors, lasers, and magnetic resonance imaging all rely on quantum principles. Current research in quantum computing promises to revolutionize information processing by exploiting superposition and entanglement to perform calculations impossible for classical computers.""",
        "source": "wikipedia",
        "source_name": "Wikipedia",
        "url": "https://en.wikipedia.org/wiki/Quantum_mechanics",
        "difficulty_level": "C1",
        "difficulty_score": 9.5,
        "word_count": 238,
        "key_vocabulary": ["quantum mechanics", "wave-particle duality", "uncertainty principle", "entanglement", "superposition"],
        "topics": ["science", "physics", "quantum theory"]
    },
    {
        "title": "Learning a New Language",
        "content": """Learning a new language is fun and useful. It helps you talk to more people and understand different cultures. Many people learn English, Spanish, or Chinese.

There are many ways to learn a language. You can take classes at school or use apps on your phone. Watching movies and listening to music in the new language also helps. The most important thing is to practice every day.

When you start learning, don't worry about making mistakes. Everyone makes mistakes when learning something new. The more you practice, the better you will become. Try to speak with native speakers when you can.

Learning a language takes time, but it's worth it. You will feel proud when you can have a conversation in a new language.""",
        "source": "wikipedia",
        "source_name": "Wikipedia",
        "url": "https://en.wikipedia.org/wiki/Language_learning",
        "difficulty_level": "A1",
        "difficulty_score": 2.8,
        "word_count": 135,
        "key_vocabulary": ["learn", "language", "practice", "culture", "mistakes"],
        "topics": ["education", "language", "learning"]
    },
    {
        "title": "Artificial Intelligence in Modern Society",
        "content": """Artificial Intelligence (AI) is rapidly transforming various sectors of modern society, from healthcare and finance to transportation and entertainment. Machine learning algorithms can now analyze vast datasets to identify patterns and make predictions with remarkable accuracy, often surpassing human capabilities in specific tasks.

In healthcare, AI systems assist in diagnosing diseases, analyzing medical images, and predicting patient outcomes. Deep learning models can detect subtle patterns in X-rays and MRI scans that might escape human observation. Personalized treatment recommendations based on genetic profiles and medical histories are becoming increasingly sophisticated.

The financial sector employs AI for fraud detection, algorithmic trading, and risk assessment. These systems can process millions of transactions in real-time, identifying suspicious activities and market trends. Chatbots and virtual assistants handle customer inquiries, providing instant responses and personalized financial advice.

However, the proliferation of AI raises important ethical considerations. Concerns about algorithmic bias, data privacy, and the displacement of human workers require careful attention. Ensuring that AI systems are transparent, fair, and accountable is crucial for maintaining public trust.

As AI technology continues to advance, society must balance innovation with responsibility, establishing regulatory frameworks that promote beneficial applications while mitigating potential harms.""",
        "source": "wikipedia",
        "source_name": "Wikipedia",
        "url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
        "difficulty_level": "C2",
        "difficulty_score": 10.0,
        "word_count": 198,
        "key_vocabulary": ["artificial intelligence", "machine learning", "algorithm", "ethical considerations", "algorithmic bias"],
        "topics": ["technology", "AI", "ethics", "society"]
    }
]


def import_articles():
    """导入测试文章"""
    print("🚀 开始导入测试文章...")
    
    # 初始化数据库
    db_path = os.getenv('DATABASE_URL', 'sqlite:///backend/english_learning.db')
    engine = init_db(db_path)
    session = get_session(engine)
    
    try:
        # 检查现有文章
        existing_count = session.query(Article).count()
        print(f"📊 当前数据库中有 {existing_count} 篇文章")
        
        # 导入新文章
        imported = 0
        for article_data in SAMPLE_ARTICLES:
            # 检查是否已存在
            existing = session.query(Article).filter(
                Article.title == article_data['title']
            ).first()
            
            if existing:
                print(f"⏭️  跳过已存在: {article_data['title']}")
                continue
            
            # 创建文章
            article = Article(
                title=article_data['title'],
                content=article_data['content'],
                source=article_data['source'],
                source_name=article_data.get('source_name'),
                url=article_data.get('url'),
                difficulty_level=article_data['difficulty_level'],
                difficulty_score=article_data['difficulty_score'],
                word_count=article_data['word_count'],
                key_words=article_data.get('key_vocabulary'),  # 使用 key_words 字段
                category=article_data.get('topics', [])[0] if article_data.get('topics') else None,
                published_at=datetime.now(),
                created_at=datetime.now()
            )
            
            session.add(article)
            imported += 1
            print(f"✅ 已导入: {article_data['title']} ({article_data['difficulty_level']})")
        
        session.commit()
        
        # 统计
        final_count = session.query(Article).count()
        print(f"\n{'='*50}")
        print(f"✨ 导入完成！")
        print(f"📈 新增文章: {imported} 篇")
        print(f"📚 总文章数: {final_count} 篇")
        print(f"{'='*50}")
        
        # 显示各难度级别的文章数量
        print("\n难度分布:")
        for level in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
            count = session.query(Article).filter(Article.difficulty_level == level).count()
            if count > 0:
                print(f"  {level}: {count} 篇")
        
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    import_articles()
