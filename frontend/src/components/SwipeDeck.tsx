// src/components/SwipeDeck.tsx
import React, { useState } from 'react';
import { X, Heart, Info, Clock, BarChart } from 'lucide-react';
import type { Article } from '../types';

interface SwipeDeckProps {
    articles: Article[];
    onSwipeLeft: (article: Article) => void;
    onSwipeRight: (article: Article) => void;
    onSelect: (article: Article) => void;
}

const SwipeDeck: React.FC<SwipeDeckProps> = ({ articles, onSwipeLeft, onSwipeRight, onSelect }) => {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [swipeDir, setSwipeDir] = useState<'left' | 'right' | null>(null);

    const currentArticle = articles[currentIndex];

    const handleSwipe = (direction: 'left' | 'right') => {
        setSwipeDir(direction);
        setTimeout(() => {
            if (direction === 'left') onSwipeLeft(currentArticle);
            else onSwipeRight(currentArticle);

            setSwipeDir(null);
            setCurrentIndex(prev => prev + 1);
        }, 300);
    };

    if (currentIndex >= articles.length) {
        return (
            <div className="flex flex-col items-center justify-center h-full p-8 text-center space-y-4">
                <div className="w-20 h-20 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center">
                    <Info className="text-slate-400" size={32} />
                </div>
                <h3 className="text-xl font-bold dark:text-white">No more articles</h3>
                <p className="text-slate-500 max-w-xs">You've seen all the recommendations for now. Check back later or browse the library.</p>
                <button
                    onClick={() => setCurrentIndex(0)}
                    className="px-6 py-2 bg-blue-600 text-white rounded-full font-semibold"
                >
                    Reset Deck
                </button>
            </div>
        );
    }

    return (
        <div className="relative w-full max-w-md mx-auto h-[600px] mt-8">
            {/* Background hint card */}
            {currentIndex + 1 < articles.length && (
                <div className="absolute inset-0 scale-95 translate-y-4 opacity-50 bg-slate-200 dark:bg-slate-800 rounded-3xl blur-[1px]" />
            )}

            {/* Main Card */}
            <div
                className={`absolute inset-0 bg-white dark:bg-slate-900 rounded-3xl shadow-2xl border border-slate-100 dark:border-slate-800 overflow-hidden cursor-pointer transition-all duration-300 transform ${swipeDir === 'left' ? '-translate-x-[150%] -rotate-12' :
                    swipeDir === 'right' ? 'translate-x-[150%] rotate-12' : 'scale-100'
                    }`}
                onClick={() => onSelect(currentArticle)}
            >
                <div className="relative h-3/5 overflow-hidden">
                    {currentArticle.imageUrl ? (
                        <img
                            src={currentArticle.imageUrl}
                            alt={currentArticle.title}
                            className="w-full h-full object-cover"
                        />
                    ) : (
                        <div className="w-full h-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-300">
                            <BarChart size={64} />
                        </div>
                    )}
                    <div className="absolute top-6 left-6 flex space-x-2">
                        <span className="px-3 py-1 bg-blue-600 text-white backdrop-blur-md text-[10px] font-black uppercase tracking-wider rounded-full shadow-md">
                            {currentArticle.source}
                        </span>
                        <span className="px-3 py-1 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md text-[10px] font-bold rounded-full shadow-md text-slate-900 dark:text-white uppercase tracking-wider">
                            {currentArticle.category}
                        </span>
                    </div>

                    {/* Swipe text indicators */}
                    {swipeDir === 'right' && (
                        <div className="absolute top-12 left-12 border-4 border-emerald-500 text-emerald-500 font-black text-4xl px-4 py-2 rounded-xl rotate-[-20deg] animate-pulse">
                            SAVE
                        </div>
                    )}
                    {swipeDir === 'left' && (
                        <div className="absolute top-12 right-12 border-4 border-red-500 text-red-500 font-black text-4xl px-4 py-2 rounded-xl rotate-[20deg] animate-pulse">
                            SKIP
                        </div>
                    )}
                </div>

                <div className="p-8 h-2/5 flex flex-col justify-between">
                    <div>
                        <h2 className="text-2xl font-bold text-slate-900 dark:text-white line-clamp-2 leading-tight mb-2">
                            {currentArticle.title}
                        </h2>
                        <div className="flex items-center space-x-4 text-slate-500 text-sm font-medium">
                            <div className="flex items-center space-x-1.5">
                                <Clock size={16} className="text-slate-400" />
                                <span>{currentArticle.readTimeMin || 5} min read</span>
                            </div>
                            <div className="flex items-center space-x-1.5">
                                <BarChart size={16} className="text-blue-500" />
                                <span>{currentArticle.difficulty_level}</span>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center justify-center space-x-8 pt-4">
                        <button
                            onClick={(e) => { e.stopPropagation(); handleSwipe('left'); }}
                            className="w-16 h-16 rounded-full border-2 border-slate-100 dark:border-slate-700 flex items-center justify-center text-red-500 hover:bg-red-50 dark:hover:bg-red-900/10 transition-colors shadow-sm"
                        >
                            <X size={32} />
                        </button>
                        <button
                            onClick={(e) => { e.stopPropagation(); handleSwipe('right'); }}
                            className="w-16 h-16 rounded-full border-2 border-slate-100 dark:border-slate-700 flex items-center justify-center text-emerald-500 hover:bg-emerald-50 dark:hover:bg-emerald-900/10 transition-colors shadow-sm"
                        >
                            <Heart size={32} />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SwipeDeck;
