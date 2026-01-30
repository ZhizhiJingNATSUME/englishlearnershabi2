"""
添加示例文章到数据库
"""
import sys
import os
from datetime import datetime

# 添加 backend 到路径
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

from models import init_db, Article
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 示例文章数据
SAMPLE_ARTICLES = [
    {
        "title": "The Benefits of Learning a New Language",
        "content": """Learning a new language is one of the most rewarding experiences you can have. It opens doors to new cultures, helps you connect with people from different backgrounds, and enhances your cognitive abilities.

Research has shown that bilingual individuals often have better memory, problem-solving skills, and multitasking abilities. When you learn a new language, your brain creates new neural pathways, which can help delay the onset of age-related cognitive decline.

Moreover, knowing multiple languages can significantly boost your career prospects. In today's globalized world, employers highly value employees who can communicate in more than one language. This skill can lead to better job opportunities and higher salaries.

Beyond practical benefits, language learning is also culturally enriching. It allows you to enjoy literature, films, and music in their original form, giving you a deeper appreciation of different cultures. You can travel more confidently and form meaningful connections with people around the world.

Starting to learn a new language might seem challenging at first, but with consistent practice and the right resources, anyone can become proficient. The key is to stay motivated and make language learning a regular part of your daily routine.""",
        "source": "Educational Content",
        "url": "sample://article/1",
        "level": "B1",
        "word_count": 195
    },
    {
        "title": "Climate Change and Its Impact on Wildlife",
        "content": """Climate change is one of the most pressing environmental challenges of our time, and its effects on wildlife are becoming increasingly evident. Rising temperatures, changing precipitation patterns, and extreme weather events are disrupting ecosystems worldwide.

Many species are struggling to adapt to these rapid changes. Polar bears, for instance, are losing their sea ice habitat, making it harder for them to hunt seals, their primary food source. Similarly, coral reefs are experiencing widespread bleaching due to warmer ocean temperatures, threatening the diverse marine life that depends on them.

Bird migration patterns are also being affected. Some species are arriving at their breeding grounds earlier than usual, only to find that the insects they feed on haven't emerged yet. This mismatch can lead to reduced breeding success and declining populations.

Scientists are working to understand these changes and develop conservation strategies to help vulnerable species. This includes creating wildlife corridors to allow animals to move to more suitable habitats, restoring degraded ecosystems, and reducing other stressors like pollution and habitat destruction.

Individual actions also matter. By reducing our carbon footprint, supporting conservation organizations, and advocating for climate policies, we can all contribute to protecting wildlife for future generations.""",
        "source": "Environmental Studies",
        "url": "sample://article/2",
        "level": "B2",
        "word_count": 210
    },
    {
        "title": "The History of Coffee",
        "content": """Coffee is one of the world's most popular beverages, enjoyed by millions of people every day. But have you ever wondered where coffee comes from and how it became so popular?

The story of coffee begins in Ethiopia, where legend says a goat herder named Kaldi discovered coffee beans around the 9th century. He noticed that his goats became energetic after eating berries from a certain tree. Curious, he tried the berries himself and felt more alert.

From Ethiopia, coffee spread to the Arabian Peninsula, where it was first cultivated and traded. By the 15th century, coffee was being grown in Yemen, and coffeehouses began appearing in cities across the Middle East. These establishments became important centers for social interaction and intellectual discussion.

Coffee reached Europe in the 17th century, where it quickly became popular. The first coffeehouse in England opened in Oxford in 1650, and soon coffeehouses were everywhere in major European cities. In the Americas, coffee cultivation began in the 18th century and became a major industry.

Today, coffee is grown in over 70 countries, primarily in regions near the equator. It remains an important part of many cultures and continues to bring people together around the world.""",
        "source": "Cultural History",
        "url": "sample://article/3",
        "level": "A2",
        "word_count": 215
    },
    {
        "title": "The Rise of Artificial Intelligence",
        "content": """Artificial Intelligence (AI) has evolved from a concept in science fiction to a transformative technology that is reshaping virtually every aspect of modern life. Machine learning algorithms now power everything from smartphone assistants to autonomous vehicles, and their capabilities continue to expand at an unprecedented rate.

The recent breakthroughs in deep learning have been particularly remarkable. Neural networks with billions of parameters can now generate human-like text, create realistic images, and even compose music. Large language models demonstrate an impressive ability to understand context, answer questions, and engage in sophisticated conversations.

However, this rapid advancement raises important ethical considerations. Questions about privacy, algorithmic bias, and the potential displacement of human workers demand careful attention. The decision-making processes of complex AI systems can be opaque, making it difficult to understand how they arrive at their conclusions—a phenomenon known as the "black box" problem.

Despite these challenges, AI offers tremendous potential benefits. In healthcare, AI algorithms can analyze medical images with accuracy comparable to experienced radiologists, potentially improving diagnostic outcomes. In climate science, AI helps model complex environmental systems and optimize renewable energy distribution.

As we navigate this technological revolution, it is crucial to develop robust frameworks for AI governance that balance innovation with ethical responsibility, ensuring that these powerful tools serve humanity's collective interests rather than exacerbating existing inequalities.""",
        "source": "Technology Review",
        "url": "sample://article/4",
        "level": "C1",
        "word_count": 225
    },
    {
        "title": "Healthy Eating Habits for Busy People",
        "content": """Many people find it challenging to maintain healthy eating habits when they have busy schedules. Work, family responsibilities, and other commitments often leave little time for meal planning and preparation. However, with some simple strategies, it is possible to eat well even when time is limited.

One effective approach is meal planning. Setting aside time on the weekend to plan your meals for the week can save time and reduce stress during busy weekdays. You can prepare some ingredients in advance, such as washing and cutting vegetables or cooking grains and proteins in batches.

Another helpful strategy is to keep healthy snacks readily available. Stock your desk, car, or bag with nutritious options like nuts, fruit, or whole-grain crackers. This prevents you from reaching for unhealthy convenience foods when hunger strikes.

Don't skip breakfast, even if you're in a hurry. A nutritious breakfast provides energy for the day and helps prevent overeating later. Simple options like overnight oats, smoothies, or whole-grain toast with peanut butter can be prepared quickly.

Finally, remember that healthy eating doesn't have to be perfect. Making small, consistent improvements to your diet is more sustainable than attempting drastic changes. Focus on adding more whole foods, staying hydrated, and listening to your body's hunger and fullness cues.""",
        "source": "Health & Wellness",
        "url": "sample://article/5",
        "level": "B1",
        "word_count": 230
    },
    {
        "title": "The Importance of Sleep",
        "content": """Sleep is essential for our health and well-being. When we sleep, our body repairs itself and our brain processes the information we learned during the day. Without enough sleep, we can feel tired, have difficulty concentrating, and become more easily stressed.

Most adults need between seven and nine hours of sleep each night. Children and teenagers need even more. However, many people don't get enough sleep because of busy schedules, stress, or bad sleep habits.

To improve your sleep, try to go to bed and wake up at the same time every day, even on weekends. This helps your body develop a natural sleep rhythm. Also, avoid using phones, tablets, or computers before bedtime, as the blue light from these devices can make it harder to fall asleep.

Create a comfortable sleeping environment. Your bedroom should be dark, quiet, and cool. Some people find that reading a book or taking a warm bath before bed helps them relax and fall asleep more easily.

If you continue to have trouble sleeping, talk to your doctor. Good sleep is not a luxury—it's a necessity for good health.""",
        "source": "Health Education",
        "url": "sample://article/6",
        "level": "A2",
        "word_count": 200
    }
]

def add_sample_articles():
    """添加示例文章到数据库"""
    # 初始化数据库
    db_path = os.path.join(backend_path, 'english_learning.db')
    db_url = f'sqlite:///{db_path}'
    engine = init_db(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 检查是否已有文章
        existing_count = session.query(Article).count()
        print(f"📊 当前数据库中有 {existing_count} 篇文章")
        
        added_count = 0
        for article_data in SAMPLE_ARTICLES:
            # 检查是否已存在相同标题的文章
            existing = session.query(Article).filter_by(title=article_data['title']).first()
            if existing:
                print(f"⏭️  跳过已存在的文章: {article_data['title']}")
                continue
            
            # 创建新文章
            article = Article(
                title=article_data['title'],
                content=article_data['content'],
                source=article_data['source'],
                url=article_data['url'],
                difficulty_level=article_data['level'],
                word_count=article_data['word_count'],
                created_at=datetime.now()
            )
            session.add(article)
            added_count += 1
            print(f"✅ 添加文章: {article_data['title']} (级别: {article_data['level']})")
        
        session.commit()
        
        new_count = session.query(Article).count()
        print(f"\n🎉 完成! 添加了 {added_count} 篇新文章")
        print(f"📊 数据库中现在共有 {new_count} 篇文章")
        
        # 显示所有文章
        print("\n📚 所有文章列表:")
        articles = session.query(Article).all()
        for i, article in enumerate(articles, 1):
            print(f"{i}. {article.title} (级别: {article.difficulty_level}, 字数: {article.word_count})")
        
    except Exception as e:
        session.rollback()
        print(f"❌ 错误: {e}")
        raise
    finally:
        session.close()

if __name__ == '__main__':
    add_sample_articles()
