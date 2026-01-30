// src/components/Reader.tsx
import React, { useState, useMemo } from 'react';
import {
    X,
    Settings,
    BookOpen,
    GraduationCap,
    Plus,
    Check
} from 'lucide-react';
import type { Article, ArticleAnalysis, HighlightItem } from '../types';
import ReactMarkdown from 'react-markdown';

interface ReaderProps {
    article: Article;
    analysis: ArticleAnalysis | null;
    onClose: () => void;
    onSaveVocabulary: (word: string, details?: {
        definition?: string;
        translation?: string;
        example_sentence?: string;
        example_translation?: string;
    }) => void;
}

const Reader: React.FC<ReaderProps> = ({ article, analysis, onClose, onSaveVocabulary }) => {
    const [mode, setMode] = useState<'clean' | 'learning'>('clean');
    const [selectedHighlight, setSelectedHighlight] = useState<HighlightItem | null>(null);
    const [addedWords, setAddedWords] = useState<Set<string>>(new Set());
    const [addingWord, setAddingWord] = useState(false);
    const fontSize = 18; // Fixed font size for now

    // Helper to escape regex special characters and normalize whitespace
    const getRegexPattern = (text: string, isWord: boolean) => {
        if (!text) return null;
        const escaped = text.trim().replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replace(/\s+/g, '\\s+');
        return isWord ? `\\b${escaped}\\b` : escaped;
    };

    // Highlighting Logic
    const segments = useMemo(() => {
        if (!analysis || mode === 'clean' || !article.content) {
            return [{ text: article.content || "", highlight: null, type: 0 }];
        }

        const content = article.content;
        const highlights = analysis.highlights;

        // Create a map of character positions to highlight IDs and types
        // 0: normal, 1: grammar, 2: vocabulary, 3: grammar anchor, 4: collocation
        const charTypeMap = new Array(content.length).fill(0);
        const charIdMap = new Array(content.length).fill(null);

        // Sort highlights by length (descending) to match longer phrases first
        const sortedHighlights = [...highlights].sort((a, b) => (b.text?.length || 0) - (a.text?.length || 0));

        // 1. Mark Grammar Patterns (Lenient matching)
        sortedHighlights.filter(h => h.type === 'grammar').forEach(h => {
            const pattern = getRegexPattern(h.text, false);
            if (!pattern) return;
            const regex = new RegExp(pattern, 'gi');
            let match;
            while ((match = regex.exec(content)) !== null) {
                for (let i = match.index; i < match.index + match[0].length; i++) {
                    charTypeMap[i] = 1;
                    charIdMap[i] = h.id;
                }
            }
        });

        // 2. Mark Vocabulary (Word boundaries)
        sortedHighlights.filter(h => h.type === 'vocabulary').forEach(h => {
            const pattern = getRegexPattern(h.text, true);
            if (!pattern) return;
            const regex = new RegExp(pattern, 'gi');
            let match;
            while ((match = regex.exec(content)) !== null) {
                for (let i = match.index; i < match.index + match[0].length; i++) {
                    if (charTypeMap[i] === 0) {
                        charTypeMap[i] = 2;
                        charIdMap[i] = h.id;
                    }
                }
            }
        });

        // 3. Mark Collocations
        sortedHighlights.filter(h => h.type === 'collocation').forEach(h => {
            const pattern = getRegexPattern(h.text, false);
            if (!pattern) return;
            const regex = new RegExp(pattern, 'gi');
            let match;
            while ((match = regex.exec(content)) !== null) {
                for (let i = match.index; i < match.index + match[0].length; i++) {
                    if (charTypeMap[i] === 0) {
                        charTypeMap[i] = 4;
                        charIdMap[i] = h.id;
                    }
                }
            }
        });

        // 4. Mark Grammar Anchors
        sortedHighlights.filter(h => h.type === 'grammar' && h.anchors).forEach(h => {
            h.anchors?.forEach(anchor => {
                const pattern = getRegexPattern(anchor, true);
                if (!pattern) return;
                const regex = new RegExp(pattern, 'gi');
                let match;
                while ((match = regex.exec(content)) !== null) {
                    const start = match.index;
                    // Check if this overlap with its parent grammar highlight
                    if (charIdMap[start] === h.id && (charTypeMap[start] === 1 || charTypeMap[start] === 3)) {
                        for (let i = start; i < start + match[0].length; i++) {
                            charTypeMap[i] = 3;
                        }
                    }
                }
            });
        });

        // Convert maps to segments
        const result = [];
        let currentText = "";
        let currentId = charIdMap[0];
        let currentType = charTypeMap[0];

        for (let i = 0; i < content.length; i++) {
            if (charIdMap[i] === currentId && charTypeMap[i] === currentType) {
                currentText += content[i];
            } else {
                result.push({
                    text: currentText,
                    highlight: currentId ? highlights.find(h => h.id === currentId) : null,
                    type: currentType
                });
                currentText = content[i];
                currentId = charIdMap[i];
                currentType = charTypeMap[i];
            }
        }

        if (currentText) {
            result.push({
                text: currentText,
                highlight: currentId ? highlights.find(h => h.id === currentId) : null,
                type: currentType
            });
        }

        return result;
    }, [article.content, analysis, mode]);

    const getHighlightClass = (type: number) => {
        switch (type) {
            case 1: return 'highlight-grammar cursor-pointer';
            case 2: return 'highlight-vocabulary cursor-pointer';
            case 3: return 'highlight-grammar-anchor cursor-pointer';
            case 4: return 'highlight-collocation cursor-pointer';
            default: return '';
        }
    };

    return (
        <div className="fixed inset-0 z-50 bg-white dark:bg-slate-950 flex flex-col md:flex-row animate-in fade-in duration-300">
            {/* ... sidebar/header code remains implicit or I should include enough context ... */}
            {/* I'll target the content rendering part mainly */}
            {/* Wait, replace_file_content works on line ranges. I should check lines again */}

            <div className="flex-1 flex flex-col relative overflow-hidden h-full">
                {/* Header... */}
                <div className="h-16 px-6 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between bg-white/80 dark:bg-slate-950/80 backdrop-blur-md z-10">
                    <button onClick={onClose} className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors">
                        <X size={20} />
                    </button>

                    <div className="flex items-center bg-slate-100 dark:bg-slate-800 p-1 rounded-xl">
                        <button
                            onClick={() => {
                                setMode('clean');
                                setSelectedHighlight(null);
                            }}
                            className={`flex items-center space-x-2 px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${mode === 'clean' ? 'bg-white dark:bg-slate-700 shadow-sm text-slate-900 dark:text-white' : 'text-slate-500'
                                }`}
                        >
                            <BookOpen size={16} />
                            <span>Clean</span>
                        </button>
                        <button
                            onClick={() => {
                                setMode('learning');
                                setSelectedHighlight(null);
                            }}
                            className={`flex items-center space-x-2 px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${mode === 'learning' ? 'bg-white dark:bg-slate-700 shadow-sm text-blue-600 dark:text-blue-400' : 'text-slate-500'
                                }`}
                        >
                            <GraduationCap size={16} />
                            <span>Learning</span>
                        </button>
                    </div>

                    <div className="flex items-center space-x-2">
                        <button className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full text-slate-500">
                            <Settings size={20} />
                        </button>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto px-6 py-12 md:px-24 lg:px-48 scroll-smooth">
                    <div className="max-w-3xl mx-auto">
                        <h1 className="text-3xl md:text-4xl font-extrabold text-slate-900 dark:text-white mb-2 leading-tight">
                            {article.title}
                        </h1>
                        <div className="flex items-center space-x-3 mb-8">
                            <span className="px-2.5 py-0.5 bg-blue-600 text-white text-[10px] font-black uppercase tracking-widest rounded shadow-sm">
                                {article.source}
                            </span>
                            <span className="text-sm font-medium text-slate-400">
                                {article.source_name || 'Original Content'}
                            </span>
                            <span className="w-1 h-1 bg-slate-300 rounded-full"></span>
                            <span className="text-sm font-bold text-slate-500 uppercase tracking-wide">
                                {article.category}
                            </span>
                        </div>

                        <div
                            className="prose prose-slate dark:prose-invert max-w-none leading-relaxed"
                            style={{ fontSize: `${fontSize}px` }}
                        >
                            {mode === 'clean' ? (
                                <ReactMarkdown>{article.content || ''}</ReactMarkdown>
                            ) : (
                                // For learning mode, we still use the segments, but we wrap in pre-wrap to preserve existing newlines
                                <div className="whitespace-pre-wrap">
                                    {segments.map((segment, idx) => (
                                        <span
                                            key={idx}
                                            className={segment.highlight ? getHighlightClass(segment.type) : ''}
                                            onClick={() => segment.highlight && setSelectedHighlight(segment.highlight)}
                                        >
                                            {segment.text}
                                        </span>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {mode === 'learning' && (
                <div className={`w-full md:w-80 lg:w-96 border-l border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 flex flex-col animate-in slide-in-from-right duration-300`}>
                    <div className="p-6 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
                        <h2 className="font-bold text-slate-900 dark:text-white flex items-center space-x-2">
                            <GraduationCap className="text-blue-600" size={20} />
                            <span>Analysis</span>
                        </h2>
                        {selectedHighlight && (
                            <button onClick={() => setSelectedHighlight(null)} className="md:hidden p-1">
                                <X size={18} />
                            </button>
                        )}
                    </div>

                    <div className="flex-1 overflow-y-auto p-6">
                        {selectedHighlight ? (
                            <div className="space-y-6 animate-in slide-in-from-right-4 duration-300">
                                <div>
                                    <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-md ${selectedHighlight.type === 'vocabulary' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400' :
                                        selectedHighlight.type === 'collocation' ? 'bg-amber-100 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400' :
                                            'bg-blue-100 text-blue-700 dark:bg-blue-950/40 dark:text-blue-400'
                                        }`}>
                                        {selectedHighlight.type}
                                    </span>
                                    <h3 className="text-2xl font-bold text-slate-900 dark:text-white mt-2">
                                        {selectedHighlight.text}
                                    </h3>
                                </div>

                                <div className="bg-white dark:bg-slate-800 rounded-2xl p-4 shadow-sm border border-slate-200 dark:border-slate-700">
                                    <p className="text-slate-700 dark:text-slate-300 leading-relaxed font-serif italic text-lg mb-4">
                                        "{selectedHighlight.explanation}"
                                    </p>
                                    {selectedHighlight.translation && (
                                        <p className="text-sm text-slate-500 border-t border-slate-100 dark:border-slate-700 pt-3">
                                            {selectedHighlight.translation}
                                        </p>
                                    )}
                                </div>

                                {selectedHighlight.type === 'vocabulary' && (
                                    (() => {
                                        const isAdded = addedWords.has(selectedHighlight.text.toLowerCase());
                                        return (
                                            <button
                                                onClick={async () => {
                                                    if (isAdded) return;
                                                    setAddingWord(true);
                                                    try {
                                                        await onSaveVocabulary(selectedHighlight.text);
                                                        setAddedWords(prev => new Set(prev).add(selectedHighlight.text.toLowerCase()));
                                                    } catch (err) {
                                                        console.error('Failed to add word:', err);
                                                    } finally {
                                                        setAddingWord(false);
                                                    }
                                                }}
                                                disabled={isAdded || addingWord}
                                                className={`w-full flex items-center justify-center space-x-2 py-3 rounded-xl font-semibold shadow-lg transition-all ${
                                                    isAdded 
                                                        ? 'bg-emerald-600 text-white cursor-default' 
                                                        : 'bg-blue-600 hover:bg-blue-700 text-white shadow-blue-500/20 active:scale-95'
                                                } ${addingWord ? 'opacity-70 cursor-wait' : ''}`}
                                            >
                                                {isAdded ? (
                                                    <>
                                                        <Check size={18} className="animate-in zoom-in duration-300" />
                                                        <span>Added to Word Bank!</span>
                                                    </>
                                                ) : (
                                                    <>
                                                        <Plus size={18} />
                                                        <span>{addingWord ? 'Adding...' : 'Add to Word Bank'}</span>
                                                    </>
                                                )}
                                            </button>
                                        );
                                    })()
                                )}
                            </div>
                        ) : (
                            <div className="h-full flex flex-col items-center justify-center text-center space-y-4 opacity-40">
                                <BookOpen size={48} className="text-slate-300" />
                                <p className="text-sm text-slate-500 px-8">
                                    Click on the highlighted text in the article to see detailed analysis, vocabulary and grammar points.
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default Reader;
