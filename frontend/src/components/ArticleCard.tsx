// src/components/ArticleCard.tsx
import React from 'react';
import { Clock, BarChart, BookOpen } from 'lucide-react';
import type { Article } from '../types';

interface ArticleCardProps {
    article: Article;
    onClick: (article: Article) => void;
}

const ArticleCard: React.FC<ArticleCardProps> = ({ article, onClick }) => {
    return (
        <div
            onClick={() => onClick(article)}
            className="group bg-white dark:bg-slate-900 rounded-2xl overflow-hidden border border-slate-200 dark:border-slate-800 hover:shadow-xl hover:-translate-y-1 transition-all duration-300 cursor-pointer"
        >
            <div className="relative h-48 overflow-hidden bg-slate-100 dark:bg-slate-800">
                {article.imageUrl ? (
                    <img
                        src={article.imageUrl}
                        alt={article.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                ) : (
                    <div className="w-full h-full flex items-center justify-center text-slate-300">
                        <BookOpen size={48} />
                    </div>
                )}
                <div className="absolute top-4 left-4 flex space-x-2">
                    <span className="px-2.5 py-1 bg-blue-600/90 text-white backdrop-blur-sm text-[10px] font-black uppercase tracking-wider rounded-lg shadow-sm">
                        {article.source}
                    </span>
                    <span className="px-2.5 py-1 bg-white/90 dark:bg-slate-900/90 backdrop-blur-sm text-[10px] font-bold uppercase tracking-wider rounded-lg shadow-sm">
                        {article.category}
                    </span>
                </div>
            </div>

            <div className="p-5">
                <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2 line-clamp-2 leading-tight group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                    {article.title}
                </h3>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-4 line-clamp-2 leading-relaxed">
                    {article.summary || article.content.substring(0, 100) + '...'}
                </p>

                <div className="flex items-center justify-between pt-4 border-t border-slate-100 dark:border-slate-800">
                    <div className="flex items-center space-x-1.5 text-xs font-medium text-slate-500">
                        <Clock size={14} />
                        <span>{article.readTimeMin || Math.ceil(article.word_count / 200)} min read</span>
                    </div>
                    <div className="flex items-center space-x-1.5 text-xs font-bold px-2 py-1 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                        <BarChart size={14} className="text-blue-500" />
                        <span>{article.difficulty_level}</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ArticleCard;
