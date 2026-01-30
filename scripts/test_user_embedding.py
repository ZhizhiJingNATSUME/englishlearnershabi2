#!/usr/bin/env python3
"""
Test Script for User Embedding Update Flow
测试用户embedding是否在点赞/点踩时正确更新
"""
import os
import sys
import json

# Add project path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend'))

from backend.models import init_db, get_session, User, Article, ReadingHistory
from backend.recommender import ArticleRecommender

def test_user_embedding_update():
    """Test the full user embedding update flow"""
    
    print("=" * 60)
    print("Testing User Embedding Update Flow")
    print("=" * 60)
    
    # Initialize
    db_url = 'sqlite:///backend/english_learning.db'
    engine = init_db(db_url)
    session = get_session(engine)
    recommender = ArticleRecommender()
    
    try:
        # Step 1: Check if we have any users
        users = session.query(User).limit(5).all()
        print(f"\n[1] Found {len(users)} users in database")
        
        if not users:
            print("❌ No users found. Please create a user first.")
            return False
        
        # Use first user for testing
        test_user = users[0]
        print(f"    Using user: {test_user.username} (ID: {test_user.id})")
        print(f"    Current user_embedding: {'Yes' if test_user.user_embedding else 'No'}")
        
        # Step 2: Check articles with embeddings
        articles_with_embedding = session.query(Article).filter(
            Article.embedding != None,
            Article.embedding != ''
        ).limit(5).all()
        
        print(f"\n[2] Found {len(articles_with_embedding)} articles with embeddings")
        
        if not articles_with_embedding:
            print("❌ No articles with embeddings found!")
            print("   Run: python scripts/backfill_embeddings.py")
            return False
        
        for a in articles_with_embedding[:3]:
            emb_len = len(json.loads(a.embedding)) if a.embedding else 0
            print(f"    - [{a.id}] {a.title[:40]}... (embedding dim: {emb_len})")
        
        # Step 3: Check existing reading history
        history = session.query(ReadingHistory).filter_by(user_id=test_user.id).all()
        liked_count = sum(1 for h in history if h.liked == 1)
        disliked_count = sum(1 for h in history if h.liked == -1)
        
        print(f"\n[3] User reading history:")
        print(f"    Total records: {len(history)}")
        print(f"    Liked: {liked_count}")
        print(f"    Disliked: {disliked_count}")
        
        # Step 4: Get user profile (this computes embedding)
        print(f"\n[4] Computing user profile...")
        profile = recommender.get_user_profile(session, test_user.id)
        
        if profile:
            print(f"    ✓ Profile computed successfully")
            print(f"    - English level: {profile['english_level']}")
            print(f"    - Interests: {profile['interests']}")
            print(f"    - Has embedding: {profile['user_embedding'] is not None}")
            print(f"    - Liked articles: {len(profile['liked_articles'])}")
            print(f"    - Read articles: {len(profile['read_articles'])}")
            
            if profile['user_embedding']:
                print(f"    - Embedding dimension: {len(profile['user_embedding'])}")
        else:
            print("    ❌ Failed to compute profile")
            return False
        
        # Step 5: Simulate a like action
        print(f"\n[5] Simulating LIKE action...")
        
        # Find an article that hasn't been read by this user
        read_article_ids = {h.article_id for h in history}
        unread_articles = [a for a in articles_with_embedding if a.id not in read_article_ids]
        
        if not unread_articles:
            print("    No unread articles with embeddings. Using first article.")
            test_article = articles_with_embedding[0]
        else:
            test_article = unread_articles[0]
        
        print(f"    Article: [{test_article.id}] {test_article.title[:40]}...")
        
        # Check if history record exists
        existing_history = session.query(ReadingHistory).filter_by(
            user_id=test_user.id,
            article_id=test_article.id
        ).first()
        
        if existing_history:
            print(f"    History exists, current liked status: {existing_history.liked}")
            existing_history.liked = 1  # Set to liked
        else:
            print(f"    Creating new history record with liked=1")
            new_history = ReadingHistory(
                user_id=test_user.id,
                article_id=test_article.id,
                liked=1,
                completion_rate=1.0
            )
            session.add(new_history)
        
        session.commit()
        print(f"    ✓ Reading history saved with liked=1")
        
        # Step 6: Update user embedding (this is what happens after like)
        print(f"\n[6] Updating user embedding...")
        
        # Store old embedding for comparison
        old_embedding = test_user.user_embedding
        
        success = recommender.update_user_embedding(session, test_user.id)
        
        if success:
            print(f"    ✓ User embedding updated successfully")
            
            # Refresh user from database
            session.refresh(test_user)
            
            if test_user.user_embedding:
                new_emb = json.loads(test_user.user_embedding)
                print(f"    - New embedding dimension: {len(new_emb)}")
                print(f"    - First 5 values: {new_emb[:5]}")
                
                if old_embedding:
                    old_emb = json.loads(old_embedding)
                    # Check if embedding changed
                    if old_emb[:5] != new_emb[:5]:
                        print(f"    ✓ Embedding values changed (as expected)")
                    else:
                        print(f"    ⚠ Embedding values unchanged")
            
            # Also check interests
            print(f"    - Updated interests: {test_user.interests}")
        else:
            print(f"    ❌ Failed to update user embedding")
            print(f"    Possible reasons:")
            print(f"    - User has no liked articles with embeddings")
            print(f"    - Less than 3 liked articles and no stored embedding")
            return False
        
        # Step 7: Verify the profile again
        print(f"\n[7] Verifying updated profile...")
        new_profile = recommender.get_user_profile(session, test_user.id)
        
        if new_profile and new_profile['user_embedding']:
            print(f"    ✓ Profile has embedding")
            print(f"    - Liked articles now: {len(new_profile['liked_articles'])}")
        
        print("\n" + "=" * 60)
        print("✅ Test completed successfully!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        session.close()


def check_prerequisites():
    """Check if prerequisites are met"""
    print("\n[Pre-check] Checking prerequisites...")
    
    db_url = 'sqlite:///backend/english_learning.db'
    engine = init_db(db_url)
    session = get_session(engine)
    
    try:
        # Check articles
        total_articles = session.query(Article).count()
        with_embedding = session.query(Article).filter(
            Article.embedding != None,
            Article.embedding != ''
        ).count()
        
        print(f"  Articles: {total_articles} total, {with_embedding} with embeddings")
        
        if with_embedding == 0:
            print("\n⚠️  No articles have embeddings!")
            print("   Run: python scripts/backfill_embeddings.py")
            return False
        
        # Check users
        users = session.query(User).count()
        print(f"  Users: {users}")
        
        if users == 0:
            print("\n⚠️  No users found!")
            print("   Create a user through the frontend or API first.")
            return False
        
        print("  ✓ Prerequisites met\n")
        return True
        
    finally:
        session.close()


if __name__ == "__main__":
    if check_prerequisites():
        test_user_embedding_update()

