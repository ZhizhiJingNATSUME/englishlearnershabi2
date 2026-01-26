// src/components/WritingCoach.tsx
import { useState, useEffect } from 'react';
import { PenTool, Send, Sparkles, BookOpen, TrendingUp, CheckCircle } from 'lucide-react';
import type { WritingTopic, WritingEvaluation, WritingSubmission } from '../types';

interface WritingCoachProps {
  userId: number;
}

export default function WritingCoach({ userId }: WritingCoachProps) {
  const [topics, setTopics] = useState<WritingTopic[]>([]);
  const [selectedTopic, setSelectedTopic] = useState<WritingTopic | null>(null);
  const [userText, setUserText] = useState('');
  const [evaluation, setEvaluation] = useState<WritingEvaluation | null>(null);
  const [history, setHistory] = useState<WritingSubmission[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeView, setActiveView] = useState<'write' | 'result' | 'history'>('write');

  // 获取话题列表
  useEffect(() => {
    fetchTopics();
    fetchHistory();
  }, []);

  const fetchTopics = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/writing/topics');
      const data = await response.json();
      setTopics(data);
    } catch (err) {
      console.error('Failed to fetch topics:', err);
    }
  };

  const fetchHistory = async () => {
    try {
      const response = await fetch(`http://localhost:5000/api/writing/history?user_id=${userId}&limit=10`);
      const data = await response.json();
      setHistory(data);
    } catch (err) {
      console.error('Failed to fetch history:', err);
    }
  };

  const handleSubmit = async () => {
    if (userText.trim().length < 20) {
      alert('Please write at least 20 characters.');
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:5000/api/writing/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: userText,
          topic: selectedTopic?.description || null,
          user_id: userId
        })
      });

      const data = await response.json();
      // 后端现在直接返回评估数据，不再嵌套在 report 中
      setEvaluation(data);
      setActiveView('result');
      fetchHistory();
    } catch (err) {
      console.error('Evaluation failed:', err);
      alert('Scoring failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const renderScoreBar = (score: number, label: string) => {
    // 雅思评分是9分制，转换为百分比显示进度条
    const percentage = (score / 9) * 100;
    return (
      <div className="space-y-1">
        <div className="flex justify-between text-sm">
          <span className="text-slate-600 dark:text-slate-400">{label}</span>
          <span className="font-bold text-blue-600 dark:text-blue-400">{score}/9</span>
        </div>
        <div className="h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 transition-all duration-500"
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6 animate-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-black text-slate-900 dark:text-white tracking-tight">
            AI Writing Coach
          </h1>
          <p className="text-slate-500 mt-2">IELTS Writing AI Coach - instant scoring & polishing</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setActiveView('write')}
            className={`px-4 py-2 rounded-xl font-semibold transition-all ${
              activeView === 'write'
                ? 'bg-blue-600 text-white shadow-lg'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
            }`}
          >
            Write
          </button>
          <button
            onClick={() => setActiveView('history')}
            className={`px-4 py-2 rounded-xl font-semibold transition-all ${
              activeView === 'history'
                ? 'bg-blue-600 text-white shadow-lg'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
            }`}
          >
            History
          </button>
        </div>
      </div>

      {/* 写作界面 */}
      {activeView === 'write' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 话题选择 */}
          <div className="lg:col-span-1 space-y-4">
            <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800">
              <div className="flex items-center gap-2 mb-4">
                <BookOpen size={20} className="text-blue-600" />
                <h3 className="font-bold text-lg dark:text-white">Choose a topic</h3>
              </div>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                <button
                  onClick={() => setSelectedTopic(null)}
                  className={`w-full text-left p-3 rounded-xl transition-all ${
                    selectedTopic === null
                      ? 'bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-500'
                      : 'bg-slate-50 dark:bg-slate-800 border border-transparent hover:border-slate-300'
                  }`}
                >
                  <div className="font-semibold text-sm dark:text-white">Free writing</div>
                  <div className="text-xs text-slate-500 mt-1">No topic</div>
                </button>
                {topics.map((topic) => (
                  <button
                    key={topic.id}
                    onClick={() => setSelectedTopic(topic)}
                    className={`w-full text-left p-3 rounded-xl transition-all ${
                      selectedTopic?.id === topic.id
                        ? 'bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-500'
                        : 'bg-slate-50 dark:bg-slate-800 border border-transparent hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-blue-600 dark:text-blue-400">
                        {topic.category}
                      </span>
                    </div>
                    <div className="font-semibold text-sm dark:text-white">{topic.title}</div>
                    <div className="text-xs text-slate-500 mt-1 line-clamp-2">
                      {topic.description}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* 写作区域 */}
          <div className="lg:col-span-2 space-y-4">
            {selectedTopic && (
              <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-2xl p-6 border border-blue-200 dark:border-blue-800">
                <div className="font-bold text-blue-900 dark:text-blue-100 mb-2">
                  {selectedTopic.title}
                </div>
                <div className="text-sm text-blue-700 dark:text-blue-300">
                  {selectedTopic.description}
                </div>
              </div>
            )}

            <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <PenTool size={20} className="text-blue-600" />
                  <h3 className="font-bold text-lg dark:text-white">Your essay</h3>
                </div>
                <div className="text-sm text-slate-500">
                  {userText.split(/\s+/).filter(w => w).length} words
                </div>
              </div>
              <textarea
                value={userText}
                onChange={(e) => setUserText(e.target.value)}
                placeholder="Start writing... (150 words recommended)"
                className="w-full h-64 p-4 bg-slate-50 dark:bg-slate-800 border-none rounded-xl resize-none focus:ring-2 focus:ring-blue-500 outline-none dark:text-white"
              />
              <button
                onClick={handleSubmit}
                disabled={isLoading || userText.trim().length < 20}
                className="mt-4 w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold py-3 rounded-xl shadow-lg transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent" />
                    AI scoring in progress...
                  </>
                ) : (
                  <>
                    <Send size={20} />
                    Submit for scoring
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 评分结果 */}
      {activeView === 'result' && evaluation && (
        <div className="space-y-6">
          <button
            onClick={() => {
              setActiveView('write');
              setUserText('');
              setEvaluation(null);
            }}
            className="text-blue-600 hover:underline font-semibold"
          >
            ← Back to writing
          </button>

          {/* 总分卡片 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl p-8 text-white shadow-xl">
              <div className="text-sm font-semibold mb-2 opacity-90">Estimated IELTS score</div>
              <div className="text-6xl font-black mb-4">{evaluation.ielts.overall}</div>
              <div className="text-sm opacity-75">IELTS Band Score</div>
            </div>
            <div className="bg-gradient-to-br from-purple-600 to-pink-600 rounded-2xl p-8 text-white shadow-xl">
              <div className="text-sm font-semibold mb-2 opacity-90">General writing score</div>
              <div className="text-6xl font-black mb-4">{evaluation.general.overall}</div>
              <div className="text-sm opacity-75">General Score</div>
            </div>
          </div>

          {/* 详细评分 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800">
              <h3 className="font-bold text-lg mb-4 dark:text-white flex items-center gap-2">
                <TrendingUp size={20} className="text-blue-600" />
                IELTS criteria
              </h3>
              <div className="space-y-4">
                {renderScoreBar(evaluation.ielts.criteria.task_response.score, 'Task response')}
                {renderScoreBar(evaluation.ielts.criteria.coherence.score, 'Coherence')}
                {renderScoreBar(evaluation.ielts.criteria.lexical.score, 'Lexical resource')}
                {renderScoreBar(evaluation.ielts.criteria.grammar.score, 'Grammar accuracy')}
              </div>
              <div className="mt-4 p-4 bg-slate-50 dark:bg-slate-800 rounded-xl">
                <div className="text-xs font-bold text-slate-500 mb-2">Comments</div>
                {Object.entries(evaluation.ielts.criteria).map(([key, val]) => (
                  <div key={key} className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                    {val.comment}
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800">
              <h3 className="font-bold text-lg mb-4 dark:text-white flex items-center gap-2">
                <CheckCircle size={20} className="text-purple-600" />
                General criteria
              </h3>
              <div className="space-y-4">
                {renderScoreBar(evaluation.general.criteria.native_phrasing.score, 'Natural phrasing')}
                {renderScoreBar(evaluation.general.criteria.grammar_accuracy.score, 'Grammar accuracy')}
                {renderScoreBar(evaluation.general.criteria.spelling.score, 'Spelling')}
              </div>
            </div>
          </div>

          {/* 总体反馈 */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800">
            <h3 className="font-bold text-lg mb-4 dark:text-white">💬 Overall feedback</h3>
            <p className="text-slate-700 dark:text-slate-300">{evaluation.overall_feedback}</p>
          </div>

          {/* AI 润色 */}
          <div className="bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 rounded-2xl p-6 border border-amber-200 dark:border-amber-800">
            <h3 className="font-bold text-lg mb-4 dark:text-white flex items-center gap-2">
              <Sparkles size={20} className="text-amber-600" />
              AI polished version
            </h3>
            <p className="text-slate-700 dark:text-slate-300 whitespace-pre-wrap">
              {evaluation.improved_version}
            </p>
          </div>
        </div>
      )}

      {/* 历史记录 */}
      {activeView === 'history' && (
        <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800">
          <h3 className="font-bold text-lg mb-4 dark:text-white">Writing history</h3>
          {history.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              No writing history yet. Start your first essay!
            </div>
          ) : (
            <div className="space-y-3">
              {history.map((item) => (
                <div
                  key={item.id}
                  className="p-4 bg-slate-50 dark:bg-slate-800 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="text-sm font-semibold dark:text-white">
                        {item.topic || 'Free writing'}
                      </div>
                      <div className="text-sm text-slate-500 mt-1">{item.preview}</div>
                      <div className="text-xs text-slate-400 mt-2">
                        {new Date(item.created_at).toLocaleString('en-US')}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-blue-600">{item.score}</div>
                      <div className="text-xs text-slate-500">IELTS</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
