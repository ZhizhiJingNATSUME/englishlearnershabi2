// src/components/Reader.tsx
import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
    X,
    Settings,
    BookOpen,
    GraduationCap,
    Plus,
    Check,
    Languages,
    Loader2,
    RotateCcw
} from 'lucide-react';
import type { Article, ArticleAnalysis, HighlightItem } from '../types';
import ReactMarkdown from 'react-markdown';
import { translateArticleSegment } from '../services/api';

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

interface TranslationSegment {
    id: string;
    original: string;
    translation?: string;
    status: 'pending' | 'loading' | 'done' | 'error';
    error?: string;
}

const Reader: React.FC<ReaderProps> = ({ article, analysis, onClose, onSaveVocabulary }) => {
    const [mode, setMode] = useState<'clean' | 'learning'>('clean');
    const [selectedHighlight, setSelectedHighlight] = useState<HighlightItem | null>(null);
    const [addedWords, setAddedWords] = useState<Set<string>>(new Set());
    const [addingWord, setAddingWord] = useState(false);
    const [isTranslationOpen, setIsTranslationOpen] = useState(false);
    const [translationSegments, setTranslationSegments] = useState<TranslationSegment[]>([]);
    const [isTranslating, setIsTranslating] = useState(false);
    const [translationProgress, setTranslationProgress] = useState({ current: 0, total: 0 });
    const [translationError, setTranslationError] = useState('');
    const [hoveredSegmentIndex, setHoveredSegmentIndex] = useState<number | null>(null);
    const fontSize = 18; // Fixed font size for now
    const translationRunRef = useRef(0);

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

    const contentSignature = useMemo(() => {
        const content = article.content || '';
        return `${content.length}-${content.slice(0, 40)}-${content.slice(-40)}`;
    }, [article.content]);

    const buildTranslationSegments = (text: string) => {
        const cleaned = text.replace(/\s+/g, ' ').trim();
        if (!cleaned) return [];
        const targetWords = 80;
        const paragraphs = text.split(/\n{2,}/).map((paragraph) => paragraph.trim()).filter(Boolean);
        const result: string[] = [];
        let current: string[] = [];
        let currentWordCount = 0;

        const pushCurrent = () => {
            if (!current.length) return;
            result.push(current.join(' ').trim());
            current = [];
            currentWordCount = 0;
        };

        paragraphs.forEach((paragraph, paragraphIndex) => {
            const sentences = paragraph.split(/(?<=[.!?])\s+/);
            sentences.forEach((sentence) => {
                const wordCount = sentence.trim().split(/\s+/).filter(Boolean).length;
                if (!wordCount) return;
                if (currentWordCount + wordCount > targetWords && currentWordCount > 0) {
                    pushCurrent();
                }
                current.push(sentence.trim());
                currentWordCount += wordCount;
                if (currentWordCount >= targetWords) {
                    pushCurrent();
                }
            });
            if (paragraphIndex < paragraphs.length - 1) {
                pushCurrent();
            }
        });
        pushCurrent();
        return result;
    };

    const visualSegments = useMemo(() => {
        if (!article.content) return [];
        if (translationSegments.length > 0) {
            return translationSegments;
        }
        return buildTranslationSegments(article.content).map((segment, index) => ({
            id: `${article.id}-${index}`,
            original: segment,
            translation: '',
            status: 'pending' as const,
        }));
    }, [article.content, article.id, translationSegments]);

    useEffect(() => {
        translationRunRef.current = 0;
        setIsTranslating(false);
        setTranslationError('');
        setTranslationProgress({ current: 0, total: 0 });
        setIsTranslationOpen(false);
        const cacheKey = `article-translation-${article.id}`;
        try {
            const stored = localStorage.getItem(cacheKey);
            if (!stored) {
                setTranslationSegments([]);
                return;
            }
            const parsed = JSON.parse(stored) as { signature: string; segments: TranslationSegment[] };
            if (parsed.signature === contentSignature) {
                setTranslationSegments(parsed.segments);
            } else {
                setTranslationSegments([]);
            }
        } catch (err) {
            console.warn('Failed to load cached translation.', err);
            setTranslationSegments([]);
        }
    }, [article.id, contentSignature]);

    const persistTranslations = (segments: TranslationSegment[]) => {
        const cacheKey = `article-translation-${article.id}`;
        try {
            localStorage.setItem(cacheKey, JSON.stringify({ signature: contentSignature, segments }));
        } catch (err) {
            console.warn('Failed to cache translation.', err);
        }
    };

    const updateTranslationSegment = (index: number, update: Partial<TranslationSegment>) => {
        setTranslationSegments((prev) => {
            const next = [...prev];
            next[index] = { ...next[index], ...update };
            persistTranslations(next);
            return next;
        });
    };

    const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

    const runTranslations = async (segments: TranslationSegment[]) => {
        if (!segments.length) return;
        const runId = Date.now();
        translationRunRef.current = runId;
        setIsTranslating(true);
        setTranslationError('');
        setTranslationProgress({ current: 0, total: segments.length });
        for (let index = 0; index < segments.length; index += 1) {
            if (translationRunRef.current !== runId) return;
            const segment = segments[index];
            if (segment.status === 'done') {
                setTranslationProgress({ current: index + 1, total: segments.length });
                continue;
            }
            updateTranslationSegment(index, { status: 'loading', error: undefined });
            setTranslationProgress({ current: index + 1, total: segments.length });
            try {
                if (index > 0) {
                    await wait(350);
                }
                const response = await translateArticleSegment({ text: segment.original, target_language: 'zh-CN' });
                if (translationRunRef.current !== runId) return;
                updateTranslationSegment(index, { translation: response.translation, status: 'done' });
            } catch (err) {
                if (translationRunRef.current !== runId) return;
                const error = err as Error & { status?: number; detail?: string };
                const isRateLimited = error.status === 429 || /rate|429/i.test(error.message || '') || /rate|429/i.test(error.detail || '');
                updateTranslationSegment(index, {
                    status: 'error',
                    error: error.message || 'Translation failed',
                });
                if (isRateLimited) {
                    setTranslationError('Translation is rate-limited by the backend (HTTP 429). Please wait a moment and retry.');
                    setIsTranslating(false);
                    translationRunRef.current = 0;
                    return;
                }
                setTranslationError('Some segments failed to translate. You can retry them.');
            }
        }
        if (translationRunRef.current === runId) {
            setIsTranslating(false);
        }
    };

    const handleTranslateToggle = async () => {
        const nextOpen = !isTranslationOpen;
        setIsTranslationOpen(nextOpen);
        if (!nextOpen) {
            translationRunRef.current = 0;
            setIsTranslating(false);
            return;
        }
        if (!article.content) return;
        if (translationSegments.length === 0) {
            const segments = buildTranslationSegments(article.content).map((segment, index) => ({
                id: `${article.id}-${index}`,
                original: segment,
                status: 'pending' as const,
            }));
            setTranslationSegments(segments);
            persistTranslations(segments);
            await runTranslations(segments);
        } else {
            await runTranslations(translationSegments);
        }
    };

    const handleRefreshTranslation = async () => {
        if (!article.content) return;
        translationRunRef.current = 0;
        setIsTranslating(false);
        setTranslationError('');
        const segments = buildTranslationSegments(article.content).map((segment, index) => ({
            id: `${article.id}-${index}`,
            original: segment,
            status: 'pending' as const,
        }));
        setTranslationSegments(segments);
        persistTranslations(segments);
        setIsTranslationOpen(true);
        await runTranslations(segments);
    };

    const retrySegment = async (index: number) => {
        const segment = translationSegments[index];
        if (!segment) return;
        updateTranslationSegment(index, { status: 'loading', error: undefined });
        try {
            const response = await translateArticleSegment({ text: segment.original, target_language: 'zh-CN' });
            updateTranslationSegment(index, { translation: response.translation, status: 'done' });
        } catch (err) {
            const error = err as Error & { status?: number; detail?: string };
            const isRateLimited = error.status === 429 || /rate|429/i.test(error.message || '') || /rate|429/i.test(error.detail || '');
            updateTranslationSegment(index, {
                status: 'error',
                error: error.message || 'Translation failed',
            });
            if (isRateLimited) {
                setTranslationError('Translation is rate-limited by the backend (HTTP 429). Please wait a moment and retry.');
                return;
            }
            setTranslationError('Some segments failed to translate. You can retry them.');
        }
    };

    return (
        <div className="fixed inset-0 z-50 bg-white dark:bg-slate-950 flex flex-col md:flex-row animate-in fade-in duration-300">

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
                        <button
                            onClick={() => void handleTranslateToggle()}
                            className={`flex items-center gap-1 rounded-full px-3 py-1 text-xs font-semibold transition ${
                                isTranslationOpen
                                    ? 'bg-blue-600 text-white'
                                    : 'bg-white text-slate-600 shadow-sm dark:bg-slate-800 dark:text-slate-200'
                            }`}
                        >
                            <Languages size={14} />
                            Translate
                        </button>
                        {isTranslationOpen && (
                            <button
                                onClick={() => void handleRefreshTranslation()}
                                className="flex items-center gap-1 rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-600 shadow-sm transition hover:bg-slate-100 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                            >
                                <RotateCcw size={14} />
                                Refresh
                            </button>
                        )}
                        <button className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full text-slate-500">
                            <Settings size={20} />
                        </button>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto px-6 py-12 md:px-24 lg:px-32 scroll-smooth">
                    <div className={`mx-auto grid gap-8 ${isTranslationOpen ? 'max-w-6xl lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]' : 'max-w-3xl'}`}>
                        <div>
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
                            {!isTranslationOpen ? (
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
                            ) : (
                                <div className="space-y-4">
                                    {visualSegments.map((segment, index) => (
                                        <div
                                            key={segment.id}
                                            className={`rounded-2xl border p-4 text-sm leading-relaxed transition ${
                                                hoveredSegmentIndex === index
                                                    ? 'border-blue-300 bg-blue-50 shadow-sm dark:border-blue-700 dark:bg-blue-900/30'
                                                    : 'border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950'
                                            }`}
                                        >
                                            <p className="whitespace-pre-wrap text-slate-800 dark:text-slate-100">
                                                {segment.original}
                                            </p>
                                        </div>
                                    ))}
                                    {translationSegments.length === 0 && (
                                        <div className="rounded-xl border border-dashed border-slate-200 px-4 py-3 text-xs text-slate-500 dark:border-slate-700">
                                            No translation yet. Tap “Translate” to begin.
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>

                        {isTranslationOpen && (
                            <div className="space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                                <div className="flex flex-wrap items-center justify-between gap-2">
                                    <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200">
                                        Translation
                                    </h3>
                                    {translationProgress.total > 0 && (
                                        <span className="text-xs text-slate-500">
                                            Translating segment {Math.min(translationProgress.current, translationProgress.total)} of {translationProgress.total}
                                        </span>
                                    )}
                                </div>
                                {translationError && (
                                    <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-600 dark:border-red-800 dark:bg-red-900/20 dark:text-red-300">
                                        {translationError}
                                    </div>
                                )}
                                <div className="space-y-3">
                                    {translationSegments.map((segment, index) => (
                                        <div
                                            key={segment.id}
                                            onMouseEnter={() => setHoveredSegmentIndex(index)}
                                            onMouseLeave={() => setHoveredSegmentIndex(null)}
                                            className="rounded-2xl border border-slate-200 bg-white p-4 text-xs text-slate-700 shadow-sm dark:border-slate-700 dark:bg-slate-950 dark:text-slate-200"
                                        >
                                            <div className="flex items-center justify-between">
                                                <span className="text-[11px] uppercase text-slate-400">Segment {index + 1}</span>
                                                <div className="flex items-center gap-2 text-[11px] font-semibold">
                                                    {segment.status === 'loading' && (
                                                        <span className="flex items-center gap-1 text-blue-500">
                                                            <Loader2 size={12} className="animate-spin" />
                                                            Translating...
                                                        </span>
                                                    )}
                                                    {segment.status === 'pending' && (
                                                        <span className="text-slate-400">Pending</span>
                                                    )}
                                                    {segment.status === 'done' && (
                                                        <span className="text-emerald-600">Ready</span>
                                                    )}
                                                    {segment.status === 'error' && (
                                                        <span className="text-red-500">Error</span>
                                                    )}
                                                </div>
                                            </div>
                                            <div className="mt-3 rounded-xl bg-blue-50 p-4 text-xs text-slate-700 dark:bg-blue-900/30 dark:text-slate-200">
                                                {segment.status === 'loading' && (
                                                    <span className="text-blue-500">Loading translation...</span>
                                                )}
                                                {segment.status === 'pending' && (
                                                    <span className="text-slate-400">Waiting to translate</span>
                                                )}
                                                {segment.status === 'error' && (
                                                    <div className="space-y-2">
                                                        <p className="text-red-500 text-xs">{segment.error || 'Translation failed.'}</p>
                                                        <button
                                                            onClick={() => void retrySegment(index)}
                                                            className="inline-flex items-center gap-1 rounded-full bg-red-500 px-2 py-1 text-[11px] font-semibold text-white"
                                                        >
                                                            <RotateCcw size={12} />
                                                            Retry
                                                        </button>
                                                    </div>
                                                )}
                                                {segment.status === 'done' && segment.translation}
                                            </div>
                                        </div>
                                    ))}
                                    {translationSegments.length === 0 && (
                                        <div className="rounded-xl border border-dashed border-slate-200 px-4 py-3 text-xs text-slate-500 dark:border-slate-700">
                                            No translation yet. Tap “Translate” to begin.
                                        </div>
                                    )}
                                </div>
                                {isTranslating && (
                                    <div className="flex items-center gap-2 text-xs text-slate-500">
                                        <Loader2 size={14} className="animate-spin" />
                                        Translating segments sequentially...
                                    </div>
                                )}
                            </div>
                        )}
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
                        <div className="flex items-center gap-2">
                            {selectedHighlight && (
                                <button onClick={() => setSelectedHighlight(null)} className="md:hidden p-1">
                                    <X size={18} />
                                </button>
                            )}
                        </div>
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
