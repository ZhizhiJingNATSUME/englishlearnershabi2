// src/components/VocabularyList.tsx
import React from 'react';
import { BookMarked, RefreshCcw, Search, Volume2 } from 'lucide-react';
import type { LearningWord, VocabularyItem, VocabularyQuizQuestion } from '../types';

interface VocabularyListProps {
    vocabulary: VocabularyItem[];
    learningWord: LearningWord | null;
    isLearningWordLoading: boolean;
    onRefreshLearningWord: () => void;
    onAddLearningWord: () => void;
    selectedVocabList: string;
    onSelectVocabList: (listName: string) => void;
    quizQuestion: VocabularyQuizQuestion | null;
    quizAnswer: string | null;
    quizFeedback: 'correct' | 'incorrect' | null;
    onAnswerQuiz: (answer: string) => void;
    onRefreshQuiz: () => void;
}

const VocabularyList: React.FC<VocabularyListProps> = ({
    vocabulary,
    learningWord,
    isLearningWordLoading,
    onRefreshLearningWord,
    onAddLearningWord,
    selectedVocabList,
    onSelectVocabList,
    quizQuestion,
    quizAnswer,
    quizFeedback,
    onAnswerQuiz,
    onRefreshQuiz
}) => {
    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Word Bank</h1>
                    <p className="text-slate-500">Track and review words you've learned from reading.</p>
                </div>
                <div className="relative group">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors" size={18} />
                    <input
                        type="text"
                        placeholder="Search words..."
                        className="pl-10 pr-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none w-full md:w-64 transition-all"
                    />
                </div>
            </div>

            <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6">
                <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                    <div className="space-y-2">
                        <p className="text-xs font-bold uppercase tracking-widest text-slate-400">Learn new vocabulary</p>
                        <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
                            {learningWord?.word || 'Loading...'}
                        </h2>
                        {learningWord?.translation && (
                            <p className="text-sm text-emerald-600 dark:text-emerald-400 font-semibold">
                                {learningWord.translation}
                            </p>
                        )}
                    </div>
                    <div className="flex items-center gap-3">
                        <button
                            onClick={onRefreshLearningWord}
                            disabled={isLearningWordLoading}
                            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold border border-slate-200 dark:border-slate-700 rounded-xl text-slate-600 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition disabled:opacity-60"
                        >
                            <RefreshCcw size={16} className={isLearningWordLoading ? 'animate-spin' : ''} />
                            New word
                        </button>
                        <button
                            onClick={onAddLearningWord}
                            disabled={!learningWord?.word}
                            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-xl bg-blue-600 text-white hover:bg-blue-700 transition disabled:opacity-60"
                        >
                            Add to word bank
                        </button>
                    </div>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                    {['CET4', 'CET6', 'SAT', 'IELTS&TOEFL'].map(listName => (
                        <button
                            key={listName}
                            onClick={() => onSelectVocabList(listName)}
                            className={`px-3 py-1.5 rounded-xl text-xs font-bold uppercase tracking-wide border transition ${
                                selectedVocabList === listName
                                    ? 'border-blue-500 bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-200'
                                    : 'border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-300 hover:border-blue-300'
                            }`}
                        >
                            {listName}
                        </button>
                    ))}
                </div>
                <div className="mt-4 space-y-3">
                    <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                        {learningWord?.definition || 'Definition will appear here once loaded.'}
                    </p>
                    {learningWord?.example_sentence && (
                        <div className="bg-slate-50 dark:bg-slate-800/60 rounded-2xl p-4 text-sm text-slate-600 dark:text-slate-300">
                            <p className="font-semibold text-slate-800 dark:text-slate-100">Example</p>
                            <p className="mt-1 italic">{learningWord.example_sentence}</p>
                            {learningWord.example_translation && (
                                <p className="mt-2 text-emerald-600 dark:text-emerald-400">{learningWord.example_translation}</p>
                            )}
                        </div>
                    )}
                    {learningWord?.list_name && (
                        <span className="inline-flex items-center px-2 py-1 text-[10px] font-bold uppercase rounded-md bg-slate-100 dark:bg-slate-800 text-slate-500">
                            {learningWord.list_name} list
                        </span>
                    )}
                </div>
            </div>

            <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6">
                <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                    <div className="space-y-2">
                        <p className="text-xs font-bold uppercase tracking-widest text-slate-400">Quick quiz</p>
                        <h2 className="text-xl font-bold text-slate-900 dark:text-white">
                            {quizQuestion?.question || 'Need more words to start a quiz.'}
                        </h2>
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

            {vocabulary.length === 0 ? (
                <div className="bg-white dark:bg-slate-900 rounded-3xl p-12 text-center border border-dashed border-slate-200 dark:border-slate-800">
                    <BookMarked size={48} className="mx-auto text-slate-300 mb-4" />
                    <h3 className="text-lg font-semibold dark:text-white">Your word bank is empty</h3>
                    <p className="text-slate-500 max-w-xs mx-auto">Start reading and click on words you don't know to add them here.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {vocabulary.map((item, idx) => (
                        <div
                            key={idx}
                            className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 hover:shadow-md transition-shadow group"
                        >
                            <div className="flex items-start justify-between">
                                <div>
                                    <h3 className="text-xl font-bold text-slate-900 dark:text-white group-hover:text-blue-600 transition-colors">
                                        {item.word}
                                    </h3>
                                    {item.pronunciation && (
                                        <div className="flex items-center space-x-2 text-slate-400 text-sm mt-1">
                                            <Volume2 size={14} className="hover:text-blue-500 cursor-pointer" />
                                            <span>{item.pronunciation}</span>
                                        </div>
                                    )}
                                </div>
                                {item.cefr && (
                                    <span className="px-2 py-0.5 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 text-[10px] font-black rounded-md uppercase">
                                        {item.cefr}
                                    </span>
                                )}
                            </div>
                            <p className="mt-3 text-sm text-slate-600 dark:text-slate-400 leading-relaxed italic border-l-2 border-slate-100 dark:border-slate-800 pl-3">
                                {item.definition || 'No definition available.'}
                            </p>
                            {(item.translation || item.example_sentence) && (
                                <div className="mt-3 text-xs text-slate-500 dark:text-slate-400 space-y-2">
                                    {item.translation && (
                                        <p className="font-semibold text-emerald-600 dark:text-emerald-400">{item.translation}</p>
                                    )}
                                    {item.example_sentence && (
                                        <div className="bg-slate-50 dark:bg-slate-800/60 rounded-xl p-3">
                                            <p className="italic">{item.example_sentence}</p>
                                            {item.example_translation && (
                                                <p className="mt-2 text-emerald-600 dark:text-emerald-400">{item.example_translation}</p>
                                            )}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default VocabularyList;
