// src/components/VocabularyPractice.tsx
import React from 'react';
import { RefreshCcw } from 'lucide-react';
import type { VocabularyQuizQuestion } from '../types';

interface VocabularyPracticeProps {
    quizQuestion: VocabularyQuizQuestion | null;
    quizAnswer: string | null;
    quizFeedback: 'correct' | 'incorrect' | null;
    onAnswerQuiz: (answer: string) => void;
    onRefreshQuiz: () => void;
}

const VocabularyPractice: React.FC<VocabularyPracticeProps> = ({
    quizQuestion,
    quizAnswer,
    quizFeedback,
    onAnswerQuiz,
    onRefreshQuiz
}) => {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Vocabulary Test</h1>
                <p className="text-slate-500">Practice recall with quick multiple-choice questions.</p>
            </div>

            <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6">
                <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                    <div className="space-y-2">
                        <p className="text-xs font-bold uppercase tracking-widest text-slate-400">Practice</p>
                        <h2 className="text-xl font-bold text-slate-900 dark:text-white">Quick quiz</h2>
                        <p className="text-sm text-slate-500">
                            {quizQuestion?.question || 'Need more words to start a quiz.'}
                        </p>
                    </div>
                    <button
                        onClick={onRefreshQuiz}
                        className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold border border-slate-200 dark:border-slate-700 rounded-xl text-slate-600 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition"
                    >
                        <RefreshCcw size={16} />
                        New quiz
                    </button>
                </div>
                {quizQuestion?.options && (
                    <div className="mt-4 grid gap-2 md:grid-cols-2">
                        {quizQuestion.options.map(option => {
                            const isSelected = quizAnswer === option;
                            const isCorrect = quizFeedback === 'correct' && option === quizQuestion.answer;
                            const isIncorrect = quizFeedback === 'incorrect' && isSelected;
                            return (
                                <button
                                    key={option}
                                    onClick={() => onAnswerQuiz(option)}
                                    className={`rounded-xl border px-4 py-3 text-left text-sm font-semibold transition ${
                                        isCorrect
                                            ? 'border-emerald-400 bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
                                            : isIncorrect
                                                ? 'border-red-400 bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-300'
                                                : isSelected
                                                    ? 'border-blue-400 bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                                                    : 'border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-200 hover:border-blue-300'
                                    }`}
                                >
                                    {option}
                                </button>
                            );
                        })}
                    </div>
                )}
                {quizFeedback && quizQuestion && (
                    <p className={`mt-3 text-sm font-semibold ${quizFeedback === 'correct' ? 'text-emerald-600' : 'text-red-500'}`}>
                        {quizFeedback === 'correct' ? 'Correct! 🎉' : `Incorrect. Answer: ${quizQuestion.answer}`}
                    </p>
                )}
            </div>
        </div>
    );
};

export default VocabularyPractice;
