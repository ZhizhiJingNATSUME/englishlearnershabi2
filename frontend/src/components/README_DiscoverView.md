# Discover View - Swipe-Based Smart Recommendation System

## Overview
The Discover View is an intelligent article recommendation interface with a **Tinder-style swipe mechanism** that learns from user interactions to provide personalized content recommendations in real-time.

## Features

### 1. **User Profile Display**
- Shows user's English level, reading stats, and profile status
- Displays top interests with percentage scores
- Indicates whether user embedding is built (profile learning status)
- Real-time stats: liked articles, skipped articles, total reading time
- Quick refresh button to reload recommendations

### 2. **Interactive Topic Selection**
- 8 standardized categories: technology, science, health, business, education, culture, sports, entertainment
- Pre-selected based on user's interest profile
- Click to toggle topics for new article fetching
- Fetch new articles from multiple sources (NewsAPI, VOA, Wikipedia)

### 3. **Swipe-Based Interface** 🎴
**One article at a time - Swipe to decide!**
- **Swipe Right (❤️)** or **Click Heart Button**: Like the article
- **Swipe Left (✖️)** or **Click X Button**: Skip the article
- **Click on Card**: Open article in reader
- Beautiful card design with:
  - Large hero image
  - Source, category, and difficulty badges
  - Article title and metadata
  - Match score (when enabled)
  - Detailed recommendation reasons
- **Visual Feedback**:
  - "LIKE" stamp appears on right swipe
  - "SKIP" stamp appears on left swipe
  - Toast notifications for each action
  - Next card preview in background

### 4. **Real-time Learning** 🧠
- **After each swipe**: 
  - System immediately updates your preference profile
  - Recommendations refresh automatically in background
  - When approaching end of queue, new recommendations load seamlessly
- **No waiting**: Continuous smooth experience
- **User profile updates**: Interests recalculated after each interaction

### 5. **Progress Tracking**
- Article counter shows current position (e.g., "3 / 20")
- "Updating..." indicator when fetching new recommendations
- "All caught up!" screen when finished with options to:
  - Load more recommendations
  - Fetch new articles

### 6. **Match Score Details** (Optional)
Toggle "Show Scores" to see why each article is recommended:
- 🎯 **Content Match**: How similar to articles you liked
- 📊 **Level Fit**: Difficulty appropriateness for your level
- ❤️ **Interest Match**: Alignment with your category preferences
- Overall match percentage (0-100%)

### 7. **Recommendation Algorithm**
Multi-signal ranking considers:
- **Content Similarity (35%)**: Matches liked articles using embeddings
- **Level Fit (25%)**: Appropriate difficulty for learning
- **Interest Match (20%)**: Category preferences
- **Engagement (10%)**: Popular articles
- **Freshness (10%)**: Recently published content

### 8. **Fetch New Articles**
- Select topics and click "Fetch New Articles"
- System retrieves from NewsAPI, VOA, Wikipedia
- Automatically scrapes, analyzes, and generates embeddings
- New articles immediately available in recommendations

## User Flow

### First Time User (Cold Start)
1. User sees first recommended article card
2. **Swipe right** to like or **swipe left** to skip
3. Next article appears immediately
4. After ~5 swipes, system builds initial profile
5. Recommendations become increasingly personalized

### Experienced User
1. System loads personalized recommendations based on reading history
2. **Each swipe** triggers:
   - Immediate visual feedback (stamp animation + toast)
   - Background profile update
   - Auto-fetch more recommendations when needed
3. Recommendations continuously improve with each interaction
4. User embedding evolves in real-time

### Typical Session
```
1. Login → See user profile with stats
2. View first recommended article
3. Swipe right ❤️ → "❤️ Liked!" → Next article loads
4. Swipe left ✖️ → "👎 Skipped" → Next article loads
5. Repeat steps 3-4
6. When queue is low, system auto-fetches more
7. When done, click "Load More" or "Fetch New Articles"
```

## API Endpoints Used

```typescript
// Get personalized recommendations
GET /api/recommend?user_id=X&limit=12

// Like/unlike an article
POST /api/reading_history
Body: {
  user_id: X,
  article_id: Y,
  liked: 1 (like) | -1 (dislike) | 0 (neutral),
  completion_rate: 1.0
}

// Get user profile
GET /api/users/{user_id}/profile

// Fetch new articles
POST /api/discover
Body: {
  user_id: X,
  categories: ['technology', 'science'],
  sources: ['newsapi', 'voa', 'wikipedia'],
  count: 2,
  language: 'English'
}

// Refresh recommendations manually
POST /api/users/{user_id}/refresh_profile
```

## Component Props

```typescript
interface DiscoverViewProps {
  userId: number;              // Current user ID
  onOpenArticle: (article: Article) => void;  // Handler to open reader
}
```

## State Management

The component manages:
- `recommendations`: List of recommended articles with scores
- `userProfile`: User stats and interests
- `selectedTopics`: Topics for fetching new articles
- `likedArticles`: Set of article IDs the user liked
- `dislikedArticles`: Set of article IDs the user disliked
- `showScores`: Toggle for detailed recommendation scores

## Implementation Details

### Backend Changes
1. **recommender.py**:
   - Updated `recommend_content_based` to return detailed scores
   - Modified `recommend_hybrid` to include score breakdown
   - Returns `recommendation_score`, `recommendation_reason`, and `recommendation_reasons` (detailed)

2. **app.py**:
   - `/api/recommend` endpoint returns articles with scores
   - `/api/users/{user_id}/profile` endpoint for user stats
   - Reading history updates trigger user embedding recalculation

### Frontend Changes
1. **DiscoverView.tsx**: New component replacing old discover view
2. **api.ts**: Added `likeArticle`, `getUserProfile`, `refreshUserProfile`
3. **types/index.ts**: Added `RecommendedArticle`, `UserProfile` interfaces
4. **App.tsx**: Integrated DiscoverView component

## Usage Example

```typescript
import { DiscoverView } from './components/DiscoverView';

<DiscoverView
  userId={user.id}
  onOpenArticle={(article) => {
    setActiveArticle(article);
    // Load analysis, etc.
  }}
/>
```

## Tips for Best Experience

1. **Build Your Profile**: Like/dislike at least 5-10 articles initially
2. **Be Honest**: Accurate likes/dislikes improve recommendations
3. **Use Show Scores**: Enable to understand why articles are recommended
4. **Fetch Regularly**: Get fresh content by fetching new articles periodically
5. **Explore Categories**: Try different topics to discover new interests

## Performance Considerations

- Recommendations load asynchronously
- User profile updates happen in background
- FAISS index provides fast similarity search
- Results cached until user interaction

## Future Enhancements

- [ ] A/B testing different recommendation algorithms
- [ ] Time-based recommendations (morning news, evening learning)
- [ ] Social features (trending among similar users)
- [ ] Difficulty progression tracking
- [ ] Reading streak bonuses
- [ ] Collaborative filtering

