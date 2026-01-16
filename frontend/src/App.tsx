// src/App.tsx
import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import SwipeDeck from './components/SwipeDeck';
import ArticleCard from './components/ArticleCard';
import Reader from './components/Reader';
import VocabularyList from './components/VocabularyList';
import ReadingTest from './components/ReadingTest';
import WritingCoach from './components/WritingCoach';
import SpeakingCoach from './components/SpeakingCoach';
import { useAuth } from './hooks/useAuth';
import * as api from './services/api';
import type { Article, ViewType, ArticleAnalysis, LearningWord, ReadingHistory, VocabularyItem, UserStats, VocabularyQuizQuestion } from './types';
import { GraduationCap, Loader2, AlertCircle } from 'lucide-react';

function App() {
  const { user, loading: authLoading, login, register, logout } = useAuth();
  const [currentView, setCurrentView] = useState<ViewType>('discover');
  const [articles, setArticles] = useState<Article[]>([]);
  const [history, setHistory] = useState<ReadingHistory[]>([]);
  const [vocabulary, setVocabulary] = useState<VocabularyItem[]>([]);
  const [learningWord, setLearningWord] = useState<LearningWord | null>(null);
  const [learningWordLoading, setLearningWordLoading] = useState(false);
  const [learningWordError, setLearningWordError] = useState('');
  const [quizQuestion, setQuizQuestion] = useState<VocabularyQuizQuestion | null>(null);
  const [quizAnswer, setQuizAnswer] = useState<string | null>(null);
  const [quizFeedback, setQuizFeedback] = useState<'correct' | 'incorrect' | null>(null);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [selectedTopics, setSelectedTopics] = useState<string[]>(['technology', 'science']);
  const [discoverMessage, setDiscoverMessage] = useState('');
  const [selectedVocabList, setSelectedVocabList] = useState('IELTS&TOEFL');

  // Reader state
  const [activeArticle, setActiveArticle] = useState<Article | null>(null);
  const [activeAnalysis, setActiveAnalysis] = useState<ArticleAnalysis | null>(null);

  // Login form state
  const [showLogin, setShowLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [error, setError] = useState('');

  // Fetch data based on view
  useEffect(() => {
    if (!user) return;

    const fetchData = async () => {
      setIsLoading(true);
      try {
        if (currentView === 'discover') {
          const res = await api.getRecommendations(user.id);
          setArticles(res.recommendations);
        } else if (currentView === 'library') {
          const res = await api.getArticles();
          setArticles(res.articles);
        } else if (currentView === 'history') {
          const res = await api.getReadingHistory(user.id);
          setHistory(res.history);
        } else if (currentView === 'vocabulary') {
          const res = await api.getVocabulary(user.id);
          setVocabulary(res.vocabulary);
          setLearningWordLoading(true);
          try {
            const word = await api.getLearningWord(selectedVocabList);
            setLearningWord(word);
            setLearningWordError('');
            const quiz = await api.getVocabularyQuiz(user.id);
            setQuizQuestion(quiz);
            setQuizAnswer(null);
            setQuizFeedback(null);
          } finally {
            setLearningWordLoading(false);
          }
        } else if (currentView === 'stats') {
          const res = await api.getUserStats(user.id);
          console.log('📊 Stats API response:', res);
          console.log('User ID:', user.id);
          setStats(res);
        }
      } catch (err) {
        console.error('Failed to fetch data:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [user, currentView, selectedVocabList]);

  const handleDiscoverFetch = async () => {
    if (!user) return;
    if (selectedTopics.length === 0) {
      setDiscoverMessage('Please select at least one topic.');
      return;
    }
    setIsDiscovering(true);
    setDiscoverMessage('');
    try {
      const res = await api.discoverArticles({
        user_id: user.id,
        categories: selectedTopics,
        sources: ['newsapi', 'voa', 'wikipedia'],
        count: 3,
        language: 'English'
      });
      setArticles(res.recommendations);
      setDiscoverMessage(`Fetched ${res.stats.total_scraped} new articles.`);
    } catch (err) {
      console.error('Discover failed:', err);
      setDiscoverMessage('Failed to fetch new articles. Please try again.');
    } finally {
      setIsDiscovering(false);
    }
  };

  const handleOpenArticle = async (article: Article) => {
    // 如果有 summary 但没有 content，或者 summary 是截断的 content
    const needsFetch = !article.content || (article.content.endsWith('...') && article.content.length < 500);

    // 如果没有 content，临时用 summary 填充以显示某种东西（虽然 Reader 可能需要完整 content）
    if (!article.content && article.summary) {
      setActiveArticle({ ...article, content: article.summary });
    } else {
      setActiveArticle(article);
    }

    try {
      // 需要获取全文
      if (needsFetch) {
        const fullArticle = await api.getArticle(article.id);
        setActiveArticle(fullArticle);
      }

      const analysis = await api.getArticleAnalysis(article.id);
      setActiveAnalysis(analysis);

      if (user) {
        await api.saveReadingHistory({
          user_id: user.id,
          article_id: article.id,
          completion_rate: 0,
          time_spent: 0
        });
      }
    } catch (err) {
      console.error('Failed to augment article data:', err);
      setActiveAnalysis(null);
    }
  };

  const handleSaveVocab = async (word: string, details?: {
    definition?: string;
    translation?: string;
    example_sentence?: string;
    example_translation?: string;
    source_article_id?: number;
  }) => {
    if (!user) return;
    try {
      await api.addVocabulary({
        user_id: user.id,
        word,
        article_id: activeArticle?.id,
        source_article_id: details?.source_article_id,
        definition: details?.definition,
        translation: details?.translation,
        example_sentence: details?.example_sentence,
        example_translation: details?.example_translation
      });
      if (currentView === 'vocabulary') {
        const res = await api.getVocabulary(user.id);
        setVocabulary(res.vocabulary);
      }
    } catch (err) {
      console.error('Failed to save vocabulary:', err);
    }
  };

  const refreshLearningWord = async () => {
    if (!user) return;
    setLearningWordLoading(true);
    try {
      const word = await api.getLearningWord(selectedVocabList);
      setLearningWord(word);
      setLearningWordError('');
    } catch (err) {
      console.error('Failed to load learning word:', err);
      setLearningWord(null);
      setLearningWordError('No words available for this list yet.');
    } finally {
      setLearningWordLoading(false);
    }
  };

  const refreshQuizQuestion = async () => {
    if (!user) return;
    try {
      const quiz = await api.getVocabularyQuiz(user.id);
      setQuizQuestion(quiz);
      setQuizAnswer(null);
      setQuizFeedback(null);
    } catch (err) {
      console.error('Failed to load vocabulary quiz:', err);
    }
  };

  const handleAddLearningWord = async () => {
    if (!learningWord?.word) return;
    await handleSaveVocab(learningWord.word, {
      definition: learningWord.definition,
      translation: learningWord.translation,
      example_sentence: learningWord.example_sentence,
      example_translation: learningWord.example_translation
    });
    await refreshLearningWord();
  };

  const handleQuizAnswer = (answer: string) => {
    if (!quizQuestion) return;
    setQuizAnswer(answer);
    setQuizFeedback(answer === quizQuestion.answer ? 'correct' : 'incorrect');
  };

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      if (showLogin) await login(username);
      else await register(username, 'B1');
    } catch (err: any) {
      setError(err.message || 'Auth failed');
    }
  };

  if (authLoading) return (
    <div className="h-screen w-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
      <Loader2 className="animate-spin text-blue-600" size={48} />
    </div>
  );

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950 p-4">
        <div className="w-full max-w-md bg-white dark:bg-slate-900 rounded-3xl shadow-2xl overflow-hidden border border-slate-100 dark:border-slate-800 animate-in zoom-in-95 duration-500">
          <div className="h-32 bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center">
            <GraduationCap className="text-white" size={64} />
          </div>
          <div className="p-8">
            <h2 className="text-2xl font-bold dark:text-white mb-2 text-center">
              {showLogin ? 'Welcome Back' : 'Join Faga'}
            </h2>
            <p className="text-slate-500 text-sm text-center mb-8">
              {showLogin ? 'Continue your English learning journey' : 'Start your adaptive learning experience'}
            </p>

            <form onSubmit={handleAuth} className="space-y-4">
              {error && (
                <div className="p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm rounded-xl flex items-center space-x-2">
                  <AlertCircle size={16} />
                  <span>{error}</span>
                </div>
              )}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-500 uppercase ml-1">Username</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter your username"
                  className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-800 border-none rounded-xl focus:ring-2 focus:ring-blue-500 outline-none transition-all dark:text-white"
                  required
                />
              </div>
              <button className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-xl shadow-lg shadow-blue-500/30 transition-all active:scale-95 mt-4">
                {showLogin ? 'Login' : 'Register'}
              </button>
            </form>

            <div className="mt-8 pt-6 border-t border-slate-100 dark:border-slate-800 text-center">
              <button
                onClick={() => setShowLogin(!showLogin)}
                className="text-sm font-semibold text-blue-600 dark:text-blue-400 hover:underline"
              >
                {showLogin ? "Don't have an account? Create one" : "Already have an account? Login"}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex transition-colors duration-500">
      <Sidebar
        currentView={currentView}
        setCurrentView={setCurrentView}
        user={user}
        onLogout={logout}
      />

      <main className="flex-1 ml-64 p-8 lg:p-12 overflow-y-auto min-h-screen">
        <div className="max-w-6xl mx-auto">
          {currentView === 'discover' && (
            <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-500">
              <div className="text-center md:text-left">
                <h1 className="text-4xl font-black text-slate-900 dark:text-white mb-2 tracking-tight">Discover</h1>
                <p className="text-slate-500">Swipe through articles picked just for your {user.english_level} level.</p>
              </div>
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 space-y-4">
                <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                  <div>
                    <h2 className="text-lg font-bold dark:text-white">Choose topics</h2>
                    <p className="text-sm text-slate-500">We will fetch the latest articles and analyze them for you.</p>
                  </div>
                  <button
                    onClick={handleDiscoverFetch}
                    disabled={isDiscovering}
                    className="inline-flex items-center justify-center px-4 py-2 rounded-xl bg-blue-600 text-white font-semibold hover:bg-blue-700 transition disabled:opacity-60"
                  >
                    {isDiscovering ? 'Fetching...' : 'Fetch latest articles'}
                  </button>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                  {['technology', 'science', 'health', 'business', 'education', 'culture', 'sports', 'environment'].map(topic => (
                    <label
                      key={topic}
                      className={`flex items-center gap-2 rounded-xl border px-3 py-2 text-sm font-semibold capitalize cursor-pointer transition ${
                        selectedTopics.includes(topic)
                          ? 'border-blue-400 bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-200'
                          : 'border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 hover:border-blue-300'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={selectedTopics.includes(topic)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedTopics([...selectedTopics, topic]);
                          } else {
                            setSelectedTopics(selectedTopics.filter(item => item !== topic));
                          }
                        }}
                        className="accent-blue-600"
                      />
                      {topic}
                    </label>
                  ))}
                </div>
                {discoverMessage && (
                  <p className="text-sm text-slate-500">{discoverMessage}</p>
                )}
              </div>
              {isLoading ? (
                <div className="flex flex-col items-center justify-center py-24 space-y-4">
                  <Loader2 className="animate-spin text-blue-600" size={48} />
                  <p className="text-slate-500 font-medium">Curating your recommendations...</p>
                </div>
              ) : (
                <SwipeDeck
                  articles={articles}
                  onSwipeLeft={() => { }}
                  onSwipeRight={() => { }}
                  onSelect={handleOpenArticle}
                />
              )}
            </div>
          )}

          {currentView === 'library' && (
            <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-500">
              <div>
                <h1 className="text-3xl font-bold dark:text-white">Article Library</h1>
                <p className="text-slate-500">Browse all available high-quality English content.</p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {articles.map(article => (
                  <ArticleCard key={article.id} article={article} onClick={handleOpenArticle} />
                ))}
              </div>
            </div>
          )}

          {currentView === 'history' && (
            <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-500">
              <h1 className="text-3xl font-bold dark:text-white">Reading History</h1>
              <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-100 dark:border-slate-800 overflow-hidden">
                <table className="w-full text-left border-collapse">
                  <thead className="bg-slate-50 dark:bg-slate-800/50">
                    <tr>
                      <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase">Article</th>
                      <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase">Read Date</th>
                      <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {history.map(item => (
                      <tr key={item.article_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors">
                        <td className="px-6 py-4 font-semibold dark:text-white">{item.title}</td>
                        <td className="px-6 py-4 text-sm text-slate-500">{new Date(item.created_at).toLocaleDateString()}</td>
                        <td className="px-6 py-4 text-right">
                          <button
                            onClick={async () => {
                              const art = await api.getArticle(item.article_id);
                              handleOpenArticle(art);
                            }}
                            className="text-blue-600 dark:text-blue-400 font-bold text-sm hover:underline"
                          >
                            Read Again
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {currentView === 'vocabulary' && (
            <div className="animate-in slide-in-from-bottom-4 duration-500">
              <VocabularyList
                vocabulary={vocabulary}
                learningWord={learningWord}
                isLearningWordLoading={learningWordLoading}
                onRefreshLearningWord={refreshLearningWord}
                onAddLearningWord={handleAddLearningWord}
                learningWordError={learningWordError}
                selectedVocabList={selectedVocabList}
                onSelectVocabList={setSelectedVocabList}
                quizQuestion={quizQuestion}
                quizAnswer={quizAnswer}
                quizFeedback={quizFeedback}
                onAnswerQuiz={handleQuizAnswer}
                onRefreshQuiz={refreshQuizQuestion}
              />
            </div>
          )}

          {currentView === 'stats' && (
            <>
              {isLoading && (
                <div className="flex items-center justify-center h-64">
                  <Loader2 className="animate-spin text-blue-600" size={48} />
                </div>
              )}
              {!isLoading && !stats && (
                <div className="flex items-center justify-center h-64 text-slate-500">
                  <p>No stats data available. Try refreshing the page.</p>
                </div>
              )}
              {!isLoading && stats && (
                <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-500 text-slate-900 dark:text-white">
                  <h1 className="text-3xl font-bold">Learning Progress</h1>
              
                  {/* 阅读统计 */}
                  <div>
                <h2 className="text-xl font-semibold mb-4 text-slate-700 dark:text-slate-300">📚 Reading Stats</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
                  {[
                    { label: 'Articles Read', value: stats.total_articles, color: 'text-blue-600' },
                    { label: 'Words Learned', value: stats.vocabulary_count, color: 'text-emerald-600' },
                    { label: 'Minutes Active', value: stats.total_time_minutes, color: 'text-amber-600' },
                    { label: 'Tests Taken', value: stats.total_reading_tests || 0, color: 'text-purple-600' },
                    { label: 'Average Score', value: stats.avg_reading_score != null ? `${stats.avg_reading_score}%` : '-', color: 'text-pink-600' },
                  ].map((stat, idx) => (
                    <div key={idx} className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-100 dark:border-slate-800 shadow-sm">
                      <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">{stat.label}</p>
                      <p className={`text-4xl font-black ${stat.color}`}>{stat.value}</p>
                    </div>
                  ))}
                </div>
                  </div>

                  {/* 写作统计 */}
                  <div>
                <h2 className="text-xl font-semibold mb-4 text-slate-700 dark:text-slate-300">✍️ Writing Stats</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
                  {[
                    { label: 'Total Essays', value: stats.total_writings || 0, color: 'text-blue-600' },
                    { label: 'Average Score', value: stats.avg_writing_score != null ? `${stats.avg_writing_score}/9` : '-', color: 'text-emerald-600' },
                    { label: 'Highest Score', value: stats.highest_writing_score != null ? `${stats.highest_writing_score}/9` : '-', color: 'text-amber-600' },
                    { label: 'Latest Score', value: stats.latest_writing_score != null ? `${stats.latest_writing_score}/9` : '-', color: 'text-purple-600' },
                    { label: 'Total Words', value: stats.total_words_written || 0, color: 'text-pink-600' },
                  ].map((stat, idx) => (
                    <div key={idx} className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-100 dark:border-slate-800 shadow-sm">
                      <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">{stat.label}</p>
                      <p className={`text-4xl font-black ${stat.color}`}>{stat.value}</p>
                    </div>
                  ))}
                </div>
                  </div>

                  {/* 口语统计 */}
                  <div>
                <h2 className="text-xl font-semibold mb-4 text-slate-700 dark:text-slate-300">🎤 Speaking Stats</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  {[
                    { label: 'Total Sessions', value: stats.total_speaking_sessions || 0, color: 'text-blue-600' },
                    { label: 'Average Band', value: stats.avg_speaking_score != null ? `${stats.avg_speaking_score}/9` : '-', color: 'text-emerald-600' },
                    { label: 'Highest Band', value: stats.highest_speaking_score != null ? `${stats.highest_speaking_score}/9` : '-', color: 'text-amber-600' },
                    { label: 'Latest Band', value: stats.latest_speaking_score != null ? `${stats.latest_speaking_score}/9` : '-', color: 'text-purple-600' },
                  ].map((stat, idx) => (
                    <div key={idx} className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-100 dark:border-slate-800 shadow-sm">
                      <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">{stat.label}</p>
                      <p className={`text-4xl font-black ${stat.color}`}>{stat.value}</p>
                    </div>
                  ))}
                </div>
                  </div>

                  {/* 阅读分类分布 */}
                  {stats.category_distribution && Object.keys(stats.category_distribution).length > 0 && (
                    <div className="bg-white dark:bg-slate-900 p-8 rounded-3xl border border-slate-100 dark:border-slate-800 shadow-sm">
                      <h2 className="text-xl font-bold mb-6">Reading Category Distribution</h2>
                      <div className="space-y-4">
                        {Object.entries(stats.category_distribution).map(([cat, count]) => (
                          <div key={cat} className="space-y-1.5">
                            <div className="flex justify-between text-sm font-medium">
                              <span className="capitalize">{cat}</span>
                              <span className="text-slate-500">{count} articles</span>
                            </div>
                            <div className="h-2 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-blue-600 rounded-full"
                                style={{ width: `${(count / (stats.total_articles || 1)) * 100}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          )}

          {currentView === 'test' && user && (
            <ReadingTest userId={user.id} />
          )}

          {currentView === 'writing' && user && (
            <WritingCoach userId={user.id} />
          )}

          {currentView === 'speaking' && user && (
            <SpeakingCoach userId={user.id} />
          )}
        </div>
      </main>

      {/* Reader Overlay */}
      {activeArticle && (
        <Reader
          article={activeArticle}
          analysis={activeAnalysis}
          onClose={() => setActiveArticle(null)}
          onSaveVocabulary={handleSaveVocab}
        />
      )}
    </div>
  );
}

export default App;
