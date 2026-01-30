import React, { useState, useEffect } from 'react';
import { X, Heart, Loader2, RefreshCw } from 'lucide-react';
import * as api from '../services/api';
import type { Article, RecommendedArticle, UserProfile } from '../types';

const UNIFIED_CATEGORIES = [
  'technology',
  'science',
  'health',
  'business',
  'education',
  'culture',
  'sports',
  'entertainment'
];

interface DiscoverViewProps {
  userId: number;
  onOpenArticle: (article: Article) => void;
}

export const DiscoverView: React.FC<DiscoverViewProps> = ({ userId, onOpenArticle }) => {
  const [recommendations, setRecommendations] = useState<RecommendedArticle[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isFetching, setIsFetching] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [message, setMessage] = useState('');
  const [showScores, setShowScores] = useState(false);
  const [swipeDir, setSwipeDir] = useState<'left' | 'right' | null>(null);
  const [swipeFeedback, setSwipeFeedback] = useState('');

  useEffect(() => {
    loadUserProfile();
    loadRecommendations();
  }, [userId]);

  const loadUserProfile = async () => {
    try {
      const profile = await api.getUserProfile(userId);
      setUserProfile(profile);
      
      // Set initial topics based on user interests
      if (profile.interests && Object.keys(profile.interests).length > 0) {
        const topInterests = Object.entries(profile.interests)
          .sort((a, b) => (b[1] as number) - (a[1] as number))
          .slice(0, 4)
          .map(([cat]) => cat);
        setSelectedTopics(topInterests);
      } else {
        // Default topics if no interests
        setSelectedTopics(['technology', 'science', 'business']);
      }
    } catch (err) {
      console.error('Failed to load user profile:', err);
    }
  };

  const loadRecommendations = async (resetIndex = true) => {
    setIsLoading(true);
    try {
      const res = await api.getRecommendations(userId, 20);
      setRecommendations(res.recommendations as RecommendedArticle[]);
      if (resetIndex) {
        setCurrentIndex(0);
      }
    } catch (err) {
      console.error('Failed to load recommendations:', err);
      setMessage('Failed to load recommendations');
    } finally {
      setIsLoading(false);
    }
  };

  const handleTopicToggle = (topic: string) => {
    setSelectedTopics(prev => 
      prev.includes(topic) 
        ? prev.filter(t => t !== topic)
        : [...prev, topic]
    );
  };

  const handleFetchNew = async () => {
    if (selectedTopics.length === 0) {
      setMessage('Please select at least one topic');
      return;
    }

    setIsFetching(true);
    setMessage('Fetching new articles...');
    try {
      const res = await api.discoverArticles({
        user_id: userId,
        categories: selectedTopics,
        sources: ['newsapi', 'voa', 'wikipedia'],
        count: 2,
        language: 'English'
      });
      setMessage(`✓ Fetched ${res.stats.total_scraped} new articles!`);
      
      // Reload recommendations to include new articles
      await loadRecommendations();
    } catch (err) {
      console.error('Discover failed:', err);
      setMessage('Failed to fetch new articles');
    } finally {
      setIsFetching(false);
    }
  };

  const handleSwipe = async (direction: 'left' | 'right') => {
    const currentArticle = recommendations[currentIndex];
    if (!currentArticle) return;

    setSwipeDir(direction);
    const isLike = direction === 'right';
    
    // Show immediate feedback
    setSwipeFeedback(isLike ? '❤️ Liked!' : '👎 Skipped');
    
    try {
      // Update preference
      await api.likeArticle(userId, currentArticle.id, isLike ? 1 : -1);
      
      // Wait for animation
      setTimeout(async () => {
        setSwipeDir(null);
        setCurrentIndex(prev => prev + 1);
        setSwipeFeedback('');
        
        // If running low on recommendations, fetch more in background
        if (currentIndex >= recommendations.length - 3) {
          setIsUpdating(true);
          try {
            const res = await api.getRecommendations(userId, 20);
            setRecommendations(res.recommendations as RecommendedArticle[]);
            // Update user profile in background
            loadUserProfile();
          } catch (err) {
            console.error('Failed to refresh recommendations:', err);
          } finally {
            setIsUpdating(false);
          }
        } else {
          // Just update profile for interest tracking
          loadUserProfile();
        }
      }, 300);
    } catch (err) {
      console.error('Failed to update preference:', err);
      setSwipeDir(null);
      setSwipeFeedback('❌ Failed to update');
      setTimeout(() => setSwipeFeedback(''), 2000);
    }
  };

  const formatScore = (score: number) => {
    return (score * 100).toFixed(0);
  };

  const currentArticle = recommendations[currentIndex];
  const hasMoreArticles = currentIndex < recommendations.length;


  return (
    <div style={{ padding: '2rem', maxWidth: '900px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '1.5rem', textAlign: 'center' }}>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
          Discover Articles
        </h1>
        <p style={{ color: '#6b7280', fontSize: '1.1rem' }}>
          Swipe right to like • Swipe left to skip
        </p>
      </div>

      {/* User Profile Card */}
      {userProfile && (
        <div style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          borderRadius: '1rem',
          padding: '1.5rem',
          marginBottom: '2rem',
          color: 'white'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            {/* Left Section: Top Interests */}
            <div style={{ flex: 1, minWidth: '250px' }}>
              {userProfile.interests && Object.keys(userProfile.interests).length > 0 ? (
                <div>
                  <div style={{ fontSize: '0.9rem', marginBottom: '0.75rem', opacity: 0.9, fontWeight: '600' }}>
                    Your Top Interests:
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {Object.entries(userProfile.interests)
                      .sort((a, b) => (b[1] as number) - (a[1] as number))
                      .slice(0, 5)
                      .map(([cat, score]) => (
                        <span
                          key={cat}
                          style={{
                            padding: '0.4rem 0.9rem',
                            background: 'rgba(255,255,255,0.25)',
                            borderRadius: '1rem',
                            fontSize: '0.9rem',
                            fontWeight: '600'
                          }}
                        >
                          {cat} {((score as number) * 100).toFixed(0)}%
                        </span>
                      ))}
                  </div>
                </div>
              ) : (
                <div style={{ fontSize: '0.95rem', opacity: 0.9 }}>
                  {!userProfile.has_embedding ? 'Learning your preferences...' : 'Start swiping to build your interests!'}
                </div>
              )}
            </div>

            {/* Right Section: Action Buttons */}
            <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
              <button
                onClick={() => setShowScores(!showScores)}
                style={{
                  padding: '0.6rem 1.2rem',
                  background: 'rgba(255,255,255,0.25)',
                  border: 'none',
                  borderRadius: '0.6rem',
                  color: 'white',
                  cursor: 'pointer',
                  fontSize: '0.9rem',
                  fontWeight: '600',
                  whiteSpace: 'nowrap'
                }}
              >
                {showScores ? 'Hide Scores' : 'Show Scores'}
              </button>
              <button
                onClick={() => loadRecommendations(true)}
                disabled={isLoading}
                style={{
                  padding: '0.6rem 1.2rem',
                  background: 'rgba(255,255,255,0.25)',
                  border: 'none',
                  borderRadius: '0.6rem',
                  color: 'white',
                  cursor: isLoading ? 'not-allowed' : 'pointer',
                  fontSize: '0.9rem',
                  fontWeight: '600',
                  whiteSpace: 'nowrap',
                  opacity: isLoading ? 0.6 : 1,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem'
                }}
              >
                <RefreshCw size={16} />
                Refresh
              </button>
            </div>
          </div>
        </div>
      )}


      {/* Swipe Feedback */}
      {swipeFeedback && (
        <div style={{
          position: 'fixed',
          top: '100px',
          left: '50%',
          transform: 'translateX(-50%)',
          padding: '1rem 2rem',
          background: 'rgba(0, 0, 0, 0.9)',
          color: 'white',
          borderRadius: '2rem',
          fontSize: '1.25rem',
          fontWeight: 'bold',
          zIndex: 1000,
          animation: 'fadeIn 0.3s'
        }}>
          {swipeFeedback}
        </div>
      )}

      {/* Loading State */}
      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '5rem 2rem', color: '#9ca3af' }}>
          <Loader2 size={48} style={{ animation: 'spin 1s linear infinite', margin: '0 auto 1rem' }} />
          <div style={{ fontSize: '1.1rem', fontWeight: '500' }}>Loading your personalized recommendations...</div>
        </div>
      ) : !hasMoreArticles ? (
        <div style={{ textAlign: 'center', padding: '5rem 2rem' }}>
          <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '0.5rem', color: '#111827' }}>
            All caught up!
          </h3>
          <p style={{ color: '#6b7280', marginBottom: '2rem', fontSize: '1.1rem' }}>
            You've seen all recommendations. Great job!
          </p>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button
              onClick={() => loadRecommendations(true)}
              style={{
                padding: '0.75rem 1.5rem',
                background: '#667eea',
                color: 'white',
                border: 'none',
                borderRadius: '0.75rem',
                cursor: 'pointer',
                fontSize: '1rem',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}
            >
              <RefreshCw size={20} />
              Load More
            </button>
          </div>
        </div>
      ) : (
        <div>
          {/* Article Counter */}
          <div style={{ 
            textAlign: 'center', 
            marginBottom: '1.5rem',
            fontSize: '0.9rem',
            color: '#6b7280',
            fontWeight: '500',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '1rem'
          }}>
            <span>
              {currentIndex + 1} / {recommendations.length}
            </span>
            {isUpdating && (
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#667eea' }}>
                <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />
                Updating...
              </span>
            )}
          </div>

          {/* Swipe Deck */}
          <div style={{ position: 'relative', width: '100%', maxWidth: '500px', height: '650px', margin: '0 auto' }}>
            {/* Background hint card */}
            {currentIndex + 1 < recommendations.length && (
              <div style={{
                position: 'absolute',
                inset: '0',
                transform: 'scale(0.95) translateY(1rem)',
                opacity: 0.5,
                background: '#e2e8f0',
                borderRadius: '1.5rem',
                filter: 'blur(1px)'
              }} />
            )}

            {/* Main Card */}
            <div style={{
              position: 'absolute',
              inset: '0',
              background: 'white',
              borderRadius: '1.5rem',
              boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
              border: '1px solid #e5e7eb',
              overflow: 'hidden',
              cursor: 'pointer',
              transition: 'all 0.3s',
              transform: swipeDir === 'left' ? 'translateX(-150%) rotate(-12deg)' :
                         swipeDir === 'right' ? 'translateX(150%) rotate(12deg)' : 'scale(1)',
              display: 'flex',
              flexDirection: 'column'
            }}>
              {/* Content Section - Now Full Height */}
              <div style={{ 
                padding: '2rem', 
                flex: 1, 
                display: 'flex', 
                flexDirection: 'column',
                position: 'relative',
                overflow: 'hidden'
              }}>
                {/* Swipe Indicators */}
                {swipeDir === 'right' && (
                  <div style={{
                    position: 'absolute',
                    top: '30%',
                    left: '10%',
                    border: '4px solid #10b981',
                    color: '#10b981',
                    fontWeight: '900',
                    fontSize: '3rem',
                    padding: '0.5rem 1rem',
                    borderRadius: '1rem',
                    transform: 'rotate(-20deg)',
                    animation: 'pulse 0.5s infinite',
                    zIndex: 10
                  }}>
                    LIKE
                  </div>
                )}
                {swipeDir === 'left' && (
                  <div style={{
                    position: 'absolute',
                    top: '30%',
                    right: '10%',
                    border: '4px solid #ef4444',
                    color: '#ef4444',
                    fontWeight: '900',
                    fontSize: '3rem',
                    padding: '0.5rem 1rem',
                    borderRadius: '1rem',
                    transform: 'rotate(20deg)',
                    animation: 'pulse 0.5s infinite',
                    zIndex: 10
                  }}>
                    SKIP
                  </div>
                )}

                {/* Badges */}
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
                  <span style={{
                    padding: '0.5rem 1rem',
                    background: '#667eea',
                    color: 'white',
                    borderRadius: '1rem',
                    fontSize: '0.75rem',
                    fontWeight: '700',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em'
                  }}>
                    {currentArticle.source_name || currentArticle.source}
                  </span>
                  <span style={{
                    padding: '0.5rem 1rem',
                    background: '#f3f4f6',
                    color: '#111827',
                    borderRadius: '1rem',
                    fontSize: '0.75rem',
                    fontWeight: '700',
                    textTransform: 'capitalize'
                  }}>
                    {currentArticle.category}
                  </span>
                  <span style={{
                    padding: '0.5rem 1rem',
                    background: '#8b5cf6',
                    color: 'white',
                    borderRadius: '1rem',
                    fontSize: '0.75rem',
                    fontWeight: '700'
                  }}>
                    {currentArticle.difficulty_level}
                  </span>
                  {showScores && currentArticle.recommendation_score && (
                    <span style={{
                      padding: '0.5rem 1rem',
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      color: 'white',
                      borderRadius: '1rem',
                      fontSize: '0.75rem',
                      fontWeight: '700'
                    }}>
                      Match: {formatScore(currentArticle.recommendation_score)}%
                    </span>
                  )}
                </div>

                {/* Scrollable Content Area */}
                <div 
                  onClick={() => onOpenArticle(currentArticle)}
                  style={{ 
                    flex: 1, 
                    overflowY: 'auto',
                    marginBottom: '1rem'
                  }}
                >
                  {/* Title */}
                  <h2 style={{
                    fontSize: '1.75rem',
                    fontWeight: '700',
                    color: '#111827',
                    lineHeight: '1.3',
                    marginBottom: '1rem'
                  }}>
                    {currentArticle.title}
                  </h2>

                  {/* Meta Info */}
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '1rem', 
                    color: '#6b7280',
                    fontSize: '0.85rem',
                    fontWeight: '500',
                    marginBottom: '1rem',
                    paddingBottom: '1rem',
                    borderBottom: '1px solid #e5e7eb'
                  }}>
                    <span>{currentArticle.word_count || 500} words</span>
                    <span>{Math.ceil((currentArticle.word_count || 500) / 200)} min read</span>
                  </div>

                  {/* Article Content Preview */}
                  {(() => {
                    const content = currentArticle.content || 'Click to read the full article...';
                    const maxChars = showScores ? 200 : 500;
                    const displayContent = content.length > maxChars ? content.substring(0, maxChars) + '...' : content;
                    
                    return (
                      <>
                        <div style={{
                          fontSize: '1rem',
                          color: '#374151',
                          lineHeight: '1.7',
                          marginBottom: '1rem'
                        }}>
                          {displayContent}
                        </div>

                        {/* Detailed Scores - Only show when showScores is true */}
                        {showScores && currentArticle.recommendation_reasons && Object.keys(currentArticle.recommendation_reasons).length > 0 && (
                          <div style={{
                            marginTop: '1rem',
                            padding: '1rem',
                            background: '#f9fafb',
                            borderRadius: '0.75rem',
                            fontSize: '0.85rem',
                            color: '#374151',
                            border: '2px solid #667eea'
                          }}>
                            <div style={{ fontWeight: '600', marginBottom: '0.75rem' }}>Why recommended:</div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                              {currentArticle.recommendation_reasons.content_similarity !== undefined && (
                                <div>Content match: {formatScore(currentArticle.recommendation_reasons.content_similarity)}%</div>
                              )}
                              {currentArticle.recommendation_reasons.level_fit !== undefined && (
                                <div>Level fit: {formatScore(currentArticle.recommendation_reasons.level_fit)}%</div>
                              )}
                              {currentArticle.recommendation_reasons.interest_match !== undefined && (
                                <div>Interest match: {formatScore(currentArticle.recommendation_reasons.interest_match)}%</div>
                              )}
                              {currentArticle.recommendation_reasons.engagement !== undefined && (
                                <div>Engagement: {formatScore(currentArticle.recommendation_reasons.engagement)}%</div>
                              )}
                              {currentArticle.recommendation_reasons.freshness !== undefined && (
                                <div>Freshness: {formatScore(currentArticle.recommendation_reasons.freshness)}%</div>
                              )}
                            </div>
                          </div>
                        )}
                      </>
                    );
                  })()}
                </div>

                {/* Action Buttons */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '2rem', paddingTop: '1rem' }}>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleSwipe('left'); }}
                    disabled={swipeDir !== null}
                    style={{
                      width: '4rem',
                      height: '4rem',
                      borderRadius: '50%',
                      border: '3px solid #ef4444',
                      background: 'white',
                      color: '#ef4444',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      cursor: swipeDir !== null ? 'not-allowed' : 'pointer',
                      transition: 'all 0.2s',
                      opacity: swipeDir !== null ? 0.5 : 1
                    }}
                    onMouseEnter={(e) => {
                      if (swipeDir === null) {
                        e.currentTarget.style.background = '#fee2e2';
                        e.currentTarget.style.transform = 'scale(1.1)';
                      }
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'white';
                      e.currentTarget.style.transform = 'scale(1)';
                    }}
                  >
                    <X size={32} strokeWidth={3} />
                  </button>

                  <button
                    onClick={(e) => { e.stopPropagation(); handleSwipe('right'); }}
                    disabled={swipeDir !== null}
                    style={{
                      width: '4rem',
                      height: '4rem',
                      borderRadius: '50%',
                      border: '3px solid #10b981',
                      background: 'white',
                      color: '#10b981',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      cursor: swipeDir !== null ? 'not-allowed' : 'pointer',
                      transition: 'all 0.2s',
                      opacity: swipeDir !== null ? 0.5 : 1
                    }}
                    onMouseEnter={(e) => {
                      if (swipeDir === null) {
                        e.currentTarget.style.background = '#d1fae5';
                        e.currentTarget.style.transform = 'scale(1.1)';
                      }
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'white';
                      e.currentTarget.style.transform = 'scale(1)';
                    }}
                  >
                    <Heart size={32} strokeWidth={3} />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add animation keyframes */}
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateX(-50%) translateY(-10px); }
          to { opacity: 1; transform: translateX(-50%) translateY(0); }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes bounce {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-20px); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.8; transform: scale(1.05); }
        }
      `}</style>
    </div>
  );
};

