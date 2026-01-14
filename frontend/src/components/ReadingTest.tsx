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
            <div className="max-w-4xl mx-auto p-6">
                <h2 className="text-2xl font-bold mb-6">📚 阅读测试</h2>

                {/* 难度选择 */}
                <div className="mb-6">
                    <label className="block text-sm font-medium mb-2">选择难度等级：</label>
                    <div className="flex gap-2">
                        {['A1', 'A2', 'B1', 'B2', 'C1', 'C2'].map(l => (
                            <button
                                key={l}
                                onClick={() => setLevel(l)}
                                className={`px-4 py-2 rounded-lg font-medium transition ${
                                    level === l
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                                }`}
                            >
                                {l}
                            </button>
                        ))}
                    </div>
                </div>

                {/* 测试类型选择 */}
                <div className="mb-6">
                    <label className="block text-sm font-medium mb-2">测试类型：</label>
                    <div className="flex gap-2">
                        <button
                            onClick={() => setTestType('cloze')}
                            className={`px-4 py-2 rounded-lg font-medium transition ${
                                testType === 'cloze'
                                    ? 'bg-green-600 text-white'
                                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                            }`}
                        >
                            完形填空
                        </button>
                        <button
                            onClick={() => setTestType('true_false')}
                            className={`px-4 py-2 rounded-lg font-medium transition ${
                                testType === 'true_false'
                                    ? 'bg-green-600 text-white'
                                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                            }`}
                        >
                            判断题
                        </button>
                    </div>
                </div>

                {/* 文章列表 */}
                <div className="space-y-4">
                    {articles.length === 0 && (
                        <p className="text-gray-500">暂无 {level} 级别的文章，请先运行数据导入</p>
                    )}
                    {articles.map((article: Article) => (
                        <div
                            key={article.id}
                            className="border rounded-lg p-4 hover:shadow-md transition cursor-pointer"
                            onClick={() => startTest(article)}
                        >
                            <div className="flex items-start justify-between">
                                <div className="flex-1">
                                    <h3 className="font-semibold text-lg mb-1">{article.title}</h3>
                                    <div className="flex gap-4 text-sm text-gray-600">
                                        <span className="flex items-center gap-1">
                                            <BookOpen size={14} />
                                            {article.word_count} 词
                                        </span>
                                        <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded">
                                            {article.difficulty_level}
                                        </span>
                                        <span className="text-gray-500">{article.category}</span>
                                    </div>
                                </div>
                                <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
                                    开始测试
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    // 测试界面
    if (step === 'test') {
        return (
            <div className="max-w-4xl mx-auto p-6">
                <div className="mb-6">
                    <h2 className="text-2xl font-bold mb-2">{selectedArticle?.title}</h2>
                    <p className="text-gray-600">
                        {testType === 'cloze' ? '完形填空' : '判断题'} · {questions.length} 题
                    </p>
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
                            <div className="border rounded-lg p-6 bg-blue-50">
                                <div className="flex items-center gap-2 mb-4">
                                    <BookOpen className="text-blue-600" size={20} />
                                    <h3 className="font-bold text-lg">阅读文章并填空</h3>
                                </div>
                                <div className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                                    {selectedArticle?.content}
                                </div>
                                <p className="text-sm text-gray-500 mt-4">
                                    💡 提示：仔细阅读文章，然后为每个空格选择正确的单词
                                </p>
                            </div>
                        )}

                        {/* 判断题：先显示完整文章 */}
                        {testType === 'true_false' && (
                            <div className="border rounded-lg p-6 bg-green-50">
                                <div className="flex items-center gap-2 mb-4">
                                    <BookOpen className="text-green-600" size={20} />
                                    <h3 className="font-bold text-lg">阅读文章</h3>
                                </div>
                                <div className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                                    {selectedArticle?.content}
                                </div>
                            </div>
                        )}

                        {/* 题目列表 */}
                        <div className="border-t-2 border-blue-600 pt-6">
                            <h3 className="font-bold text-lg mb-4">
                                {testType === 'cloze' ? '请为每个空格选择正确答案' : '判断以下陈述的正误'}
                            </h3>
                        </div>

                        {questions.map((q, idx) => (
                            <div key={q.id} className="border rounded-lg p-6 bg-white shadow-sm">
                                <h3 className="font-semibold mb-4">
                                    {testType === 'cloze' ? `空格 ${q.blank_index || idx + 1}` : `${idx + 1}. ${q.question_text}`}
                                </h3>

                                {testType === 'cloze' && q.options ? (
                                    <div className="space-y-2">
                                        {q.options.map((option, optIdx) => (
                                            <label
                                                key={optIdx}
                                                className="flex items-center gap-3 p-3 border rounded-lg hover:bg-gray-50 cursor-pointer transition"
                                            >
                                                <input
                                                    type="radio"
                                                    name={`question-${q.id}`}
                                                    value={option}
                                                    checked={answers[q.id] === option}
                                                    onChange={(e) =>
                                                        setAnswers({ ...answers, [q.id]: e.target.value })
                                                    }
                                                    className="w-4 h-4"
                                                />
                                                <span className="font-medium">{option}</span>
                                            </label>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="flex gap-4">
                                        <button
                                            onClick={() => setAnswers({ ...answers, [q.id]: 'true' })}
                                            className={`flex-1 py-3 rounded-lg font-medium transition ${
                                                answers[q.id] === 'true'
                                                    ? 'bg-green-600 text-white'
                                                    : 'bg-gray-100 hover:bg-gray-200'
                                            }`}
                                        >
                                            ✓ True
                                        </button>
                                        <button
                                            onClick={() => setAnswers({ ...answers, [q.id]: 'false' })}
                                            className={`flex-1 py-3 rounded-lg font-medium transition ${
                                                answers[q.id] === 'false'
                                                    ? 'bg-red-600 text-white'
                                                    : 'bg-gray-100 hover:bg-gray-200'
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
                                className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition"
                            >
                                取消
                            </button>
                            <button
                                onClick={submitAnswers}
                                disabled={loading}
                                className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
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
            <div className="max-w-4xl mx-auto p-6">
                <div className="text-center mb-8">
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
                    <p className="text-gray-600">
                        正确 {result.score} / {result.total} 题
                    </p>
                </div>

                <div className="space-y-4 mb-8">
                    {result.results.map((r, idx) => (
                        <div
                            key={r.question_id}
                            className={`border-l-4 p-4 rounded-r-lg ${
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
                                        <p className="text-sm text-gray-600 mt-2">💡 {r.explanation}</p>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                <button
                    onClick={resetTest}
                    className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                >
                    再做一次
                </button>
            </div>
        );
    }

    return null;
};

export default ReadingTest;
