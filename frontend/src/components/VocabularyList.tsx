// src/components/VocabularyList.tsx
import React from 'react';
import { BookMarked, Search, Volume2 } from 'lucide-react';
import type { VocabularyItem } from '../types';

interface VocabularyListProps {
    vocabulary: VocabularyItem[];
}

const VocabularyList: React.FC<VocabularyListProps> = ({ vocabulary }) => {
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
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default VocabularyList;
