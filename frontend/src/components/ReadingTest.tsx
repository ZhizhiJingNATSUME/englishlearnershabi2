// src/components/ReadingTest.tsx
import React, { useState, useEffect } from 'react';
import { BookOpen, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import * as api from '../services/api';
import type { Article, TestQuestion, TestResult } from '../types';

interface ReadingTestProps {
    userId: number;
}

const ReadingTest: React.FC<ReadingTestProps> = ({ userId }: ReadingTestProps) => {
    const [level, setLevel] = useState('B1');
    const [articles, setArticles] = useState<Article[]>([]);
    const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);
    const [testType, setTestType] = useState<'cloze' | 'true_false'>('cloze');
    const [questions, setQuestions] = useState<TestQuestion[]>([]);
    const [answers, setAnswers] = useState<Record<number, string>>({});
    const [result, setResult] = useState<TestResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [step, setStep] = useState<'select' | 'test' | 'result'>('select');

    // 加载文章列表
    useEffect(() => {
        loadArticles();
    }, [level]);

    const loadArticles = async () => {
        setLoading(true);
        try {
            const res = await api.getTestArticles(level, 10);
            setArticles(res.articles);
        } catch (err) {
            console.error('Failed to load articles:', err);
        } finally {
            setLoading(false);
        }
    };

    // 开始测试
    const startTest = async (article: Article) => {
        setLoading(true);
        setSelectedArticle(article);
        try {
            const res = await api.generateTest({
                article_id: article.id,
                question_type: testType,
                num_questions: 5
            });
            
            // 如果是完型填空，保存挖空后的文章
            if (res.article && res.article.content) {
                setSelectedArticle({
                    ...article,
                    content: res.article.content  // 挖空后的文章
                });
            }
            
            setQuestions(res.questions);
            setAnswers({});
            setStep('test');
        } catch (err) {
            console.error('Failed to generate test:', err);
            alert('生成题目失败，请重试');
        } finally {
            setLoading(false);
        }
    };

    // 提交答案
    const submitAnswers = async () => {
        if (Object.keys(answers).length < questions.length) {
            if (!confirm('还有题目未作答，确定提交吗？')) {
                return;
            }
        }

        setLoading(true);
        try {
            const answersArray = questions.map((q: TestQuestion) => ({
                question_id: q.id,
                user_answer: answers[q.id] || ''
            }));

            const res = await api.submitTest({
                user_id: userId,
                article_id: selectedArticle!.id,
                answers: answersArray,
                questions: questions
            });

            setResult(res);
            setStep('result');
        } catch (err) {
            console.error('Failed to submit test:', err);
            alert('提交失败，请重试');
        } finally {
            setLoading(false);
        }
    };

    // 重新开始
    const resetTest = () => {
        setSelectedArticle(null);
        setQuestions([]);
        setAnswers({});
        setResult(null);
        setStep('select');
        loadArticles();
    };

    if (loading && step === 'select') {
        return (
            <div className="flex items-center justify-center h-64">
                <Loader2 className="animate-spin" size={32} />
            </div>
        );
    }

    // 选择文章界面
    if (step === 'select') {
        return (
            <div className="max-w-5xl mx-auto p-6 space-y-8">
                <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-3xl p-8 text-white shadow-lg">
                    <div className="flex items-center gap-3 mb-3">
                        <BookOpen className="text-white" size={28} />
                        <h2 className="text-3xl font-bold">阅读测试</h2>
                    </div>
                    <p className="text-blue-100">
                        选择难度与题型，系统将从文章库中生成个性化阅读测试。
                    </p>
                </div>

                <div className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
                    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 space-y-6 shadow-sm">
                        <div>
                            <h3 className="text-lg font-semibold dark:text-white mb-2">选择难度等级</h3>
                            <div className="flex flex-wrap gap-2">
                                {['A1', 'A2', 'B1', 'B2', 'C1', 'C2'].map(l => (
                                    <button
                                        key={l}
                                        onClick={() => setLevel(l)}
                                        className={`px-4 py-2 rounded-xl font-semibold transition ${
                                            level === l
                                                ? 'bg-blue-600 text-white shadow-md shadow-blue-500/30'
                                                : 'bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700'
                                        }`}
                                    >
                                        {l}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div>
                            <h3 className="text-lg font-semibold dark:text-white mb-2">测试类型</h3>
                            <div className="flex flex-wrap gap-2">
                                <button
                                    onClick={() => setTestType('cloze')}
                                    className={`px-4 py-2 rounded-xl font-semibold transition ${
                                        testType === 'cloze'
                                            ? 'bg-emerald-600 text-white shadow-md shadow-emerald-500/30'
                                            : 'bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700'
                                    }`}
                                >
                                    完形填空
                                </button>
                                <button
                                    onClick={() => setTestType('true_false')}
                                    className={`px-4 py-2 rounded-xl font-semibold transition ${
                                        testType === 'true_false'
                                            ? 'bg-emerald-600 text-white shadow-md shadow-emerald-500/30'
                                            : 'bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700'
                                    }`}
                                >
                                    判断题
                                </button>
                            </div>
                        </div>
                    </div>

                    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm">
                        <h3 className="text-lg font-semibold dark:text-white mb-2">题目说明</h3>
                        <ul className="text-sm text-slate-500 space-y-2">
                            <li>• 完形填空：阅读文章后选择正确单词补全。</li>
                            <li>• 判断题：根据文章判断陈述正误。</li>
                            <li>• 每次测试 5 题，答题后即刻评分。</li>
                        </ul>
                    </div>
                </div>

                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <h3 className="text-xl font-semibold dark:text-white">可用文章</h3>
                        <span className="text-sm text-slate-500">
                            当前难度：{level} · {articles.length} 篇
                        </span>
                    </div>
                    {articles.length === 0 && (
                        <p className="text-slate-500">暂无 {level} 级别的文章，请先运行数据导入</p>
                    )}
                    <div className="grid gap-4">
                        {articles.map((article: Article) => (
                            <div
                                key={article.id}
                                className="border border-slate-200 dark:border-slate-800 rounded-2xl p-5 bg-white dark:bg-slate-900 hover:shadow-lg transition cursor-pointer"
                                onClick={() => startTest(article)}
                            >
                                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                                    <div className="space-y-2">
                                        <h4 className="text-lg font-semibold dark:text-white">{article.title}</h4>
                                        <div className="flex flex-wrap gap-2 text-sm text-slate-500">
                                            <span className="inline-flex items-center gap-1">
                                                <BookOpen size={14} />
                                                {article.word_count} 词
                                            </span>
                                            <span className="px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-200">
                                                {article.difficulty_level}
                                            </span>
                                            <span className="text-slate-400">{article.category}</span>
                                        </div>
                                    </div>
                                    <button className="px-4 py-2 rounded-xl bg-blue-600 text-white font-semibold hover:bg-blue-700 transition shadow-md shadow-blue-500/30">
                                        开始测试
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        );
    }

    // 测试界面
    if (step === 'test') {
        return (
            <div className="max-w-5xl mx-auto p-6 space-y-6">
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm">
                    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                        <div>
                            <h2 className="text-2xl font-bold dark:text-white">{selectedArticle?.title}</h2>
                            <p className="text-slate-500">
                                {testType === 'cloze' ? '完形填空' : '判断题'} · {questions.length} 题
                            </p>
                        </div>
                        <button
                            onClick={resetTest}
                            className="px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition"
                        >
                            返回选择
                        </button>
                    </div>
                </div>

                {loading ? (
                    <div className="flex items-center justify-center h-64">
                        <Loader2 className="animate-spin" size={32} />
                        <span className="ml-2">正在生成题目...</span>
                    </div>
                ) : (
                    <div className="space-y-6">
                        {/* 完形填空：先显示挖空后的文章 */}
                        {testType === 'cloze' && (
                            <div className="border border-blue-100 dark:border-blue-900/40 rounded-2xl p-6 bg-blue-50 dark:bg-blue-900/20">
                                <div className="flex items-center gap-2 mb-4">
                                    <BookOpen className="text-blue-600" size={20} />
                                    <h3 className="font-bold text-lg dark:text-white">阅读文章并填空</h3>
                                </div>
                                <div className="text-slate-800 dark:text-slate-100 leading-relaxed whitespace-pre-wrap">
                                    {selectedArticle?.content}
                                </div>
                                <p className="text-sm text-slate-500 mt-4">
                                    💡 提示：仔细阅读文章，然后为每个空格选择正确的单词
                                </p>
                            </div>
                        )}

                        {/* 判断题：先显示完整文章 */}
                        {testType === 'true_false' && (
                            <div className="border border-emerald-100 dark:border-emerald-900/40 rounded-2xl p-6 bg-emerald-50 dark:bg-emerald-900/20">
                                <div className="flex items-center gap-2 mb-4">
                                    <BookOpen className="text-green-600" size={20} />
                                    <h3 className="font-bold text-lg dark:text-white">阅读文章</h3>
                                </div>
                                <div className="text-slate-800 dark:text-slate-100 leading-relaxed whitespace-pre-wrap">
                                    {selectedArticle?.content}
                                </div>
                            </div>
                        )}

                        {/* 题目列表 */}
                        <div className="border-t border-slate-200 dark:border-slate-800 pt-6">
                            <h3 className="font-bold text-lg mb-4 dark:text-white">
                                {testType === 'cloze' ? '请为每个空格选择正确答案' : '判断以下陈述的正误'}
                            </h3>
                        </div>

                        {questions.map((q, idx) => (
                            <div key={q.id} className="border border-slate-200 dark:border-slate-800 rounded-2xl p-6 bg-white dark:bg-slate-900 shadow-sm">
                                <h3 className="font-semibold mb-4 dark:text-white">
                                    {testType === 'cloze' ? `空格 ${q.blank_index || idx + 1}` : `${idx + 1}. ${q.question_text}`}
                                </h3>

                                {testType === 'cloze' && q.options ? (
                                    <div className="space-y-2">
                                        {q.options.map((option, optIdx) => (
                                            <label
                                                key={optIdx}
                                                className="flex items-center gap-3 p-3 border border-slate-200 dark:border-slate-800 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer transition"
                                            >
                                                <input
                                                    type="radio"
                                                    name={`question-${q.id}`}
                                                    value={option}
                                                    checked={answers[q.id] === option}
                                                    onChange={(e) =>
                                                        setAnswers({ ...answers, [q.id]: e.target.value })
                                                    }
                                                    className="w-4 h-4 accent-blue-600"
                                                />
                                                <span className="font-medium dark:text-white">{option}</span>
                                            </label>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="flex gap-4">
                                        <button
                                            onClick={() => setAnswers({ ...answers, [q.id]: 'true' })}
                                            className={`flex-1 py-3 rounded-lg font-medium transition ${
                                                answers[q.id] === 'true'
                                                    ? 'bg-emerald-600 text-white'
                                                    : 'bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 dark:text-slate-200'
                                            }`}
                                        >
                                            ✓ True
                                        </button>
                                        <button
                                            onClick={() => setAnswers({ ...answers, [q.id]: 'false' })}
                                            className={`flex-1 py-3 rounded-lg font-medium transition ${
                                                answers[q.id] === 'false'
                                                    ? 'bg-red-600 text-white'
                                                    : 'bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 dark:text-slate-200'
                                            }`}
                                        >
                                            ✗ False
                                        </button>
                                    </div>
                                )}
                            </div>
                        ))}

                        <div className="flex gap-4">
                            <button
                                onClick={resetTest}
                                className="px-6 py-3 bg-slate-200 text-slate-700 rounded-xl hover:bg-slate-300 transition dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                            >
                                取消
                            </button>
                            <button
                                onClick={submitAnswers}
                                disabled={loading}
                                className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition disabled:opacity-50 shadow-md shadow-blue-500/30"
                            >
                                {loading ? '提交中...' : '提交答案'}
                            </button>
                        </div>
                    </div>
                )}
            </div>
        );
    }

    // 结果界面
    if (step === 'result' && result) {
        const percentage = result.percentage;
        const passed = percentage >= 60;

        return (
            <div className="max-w-4xl mx-auto p-6 space-y-8">
                <div className="text-center">
                    <div className={`inline-flex items-center justify-center w-24 h-24 rounded-full mb-4 ${
                        passed ? 'bg-green-100' : 'bg-red-100'
                    }`}>
                        {passed ? (
                            <CheckCircle className="text-green-600" size={48} />
                        ) : (
                            <XCircle className="text-red-600" size={48} />
                        )}
                    </div>
                    <h2 className="text-3xl font-bold mb-2">
                        {percentage.toFixed(1)}%
                    </h2>
                    <p className="text-slate-500">
                        正确 {result.score} / {result.total} 题
                    </p>
                </div>

                <div className="space-y-4">
                    {result.results.map((r, idx) => (
                        <div
                            key={r.question_id}
                            className={`border-l-4 p-4 rounded-2xl ${
                                r.is_correct ? 'border-green-500 bg-green-50' : 'border-red-500 bg-red-50'
                            }`}
                        >
                            <div className="flex items-start gap-3">
                                {r.is_correct ? (
                                    <CheckCircle className="text-green-600 flex-shrink-0 mt-1" size={20} />
                                ) : (
                                    <XCircle className="text-red-600 flex-shrink-0 mt-1" size={20} />
                                )}
                                <div className="flex-1">
                                    <p className="font-medium mb-2">
                                        第 {idx + 1} 题: {questions[idx]?.question_text}
                                    </p>
                                    {!r.is_correct && (
                                        <>
                                            <p className="text-sm text-red-700">
                                                你的答案: {r.user_answer || '(未作答)'}
                                            </p>
                                            <p className="text-sm text-green-700">
                                                正确答案: {r.correct_answer}
                                            </p>
                                        </>
                                    )}
                                    {r.explanation && (
                                        <p className="text-sm text-slate-600 mt-2">💡 {r.explanation}</p>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                <button
                    onClick={resetTest}
                    className="w-full py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition shadow-md shadow-blue-500/30"
                >
                    再做一次
                </button>
            </div>
        );
    }

    return null;
};

export default ReadingTest;
