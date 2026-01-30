// src/types/index.ts

export interface User {
    id: number;
    username: string;
    english_level: string;  // A1-C2
    learning_goal?: string;
    interests?: Record<string, number>;
}

export interface Article {
    id: number;
    title: string;
    content?: string;
    summary?: string;
    category: string;
    difficulty_level: string;
    word_count: number;
    source: string;
    source_name?: string;
    imageUrl?: string;
    readTimeMin?: number;
    created_at?: string;
}

export interface ArticleAnalysis {
    articleId: number;
    highlights: HighlightItem[];
}

export interface HighlightItem {
    id: string;
    text: string;
    type: 'vocabulary' | 'collocation' | 'grammar';
    explanation: string;
    translation?: string;
    anchors?: string[];  // 精确匹配锚点
}

export interface VocabularyItem {
    id?: number;
    word: string;
    definition?: string;
    translation?: string;
    example_sentence?: string;
    example_translation?: string;
    pronunciation?: string;
    cefr?: string;
    source_article_id?: number;
    created_at?: string;
}

export interface LearningWord {
    word: string;
    list_name?: string;
    definition?: string;
    translation?: string;
    example_sentence?: string;
    example_translation?: string;
}

export interface VocabularyQuizQuestion {
    word: string;
    question: string;
    options: string[];
    answer: string;
}

export interface DiscoverStats {
    total_fetched: number;
    total_scraped: number;
    total_analyzed: number;
    failed: number;
    duplicates: number;
}

export interface RecommendedArticle extends Article {
    recommendation_score?: number;
    recommendation_reasons?: {
        content_similarity?: number;
        level_fit?: number;
        interest_match?: number;
        engagement?: number;
        freshness?: number;
    };
}

export interface UserProfile {
    user_id: number;
    username: string;
    english_level: string;
    interests: Record<string, number>;
    has_embedding: boolean;
    liked_articles: number;
    disliked_articles: number;
    total_reading_time: number;
}

export interface ReadingHistory {
    id: number;
    article_id: number;
    title: string;
    completion_rate: number;
    time_spent: number;
    created_at: string;
}

export interface UserStats {
    // 阅读统计
    total_articles: number;
    total_time_minutes: number;
    avg_completion_rate: number;
    vocabulary_count: number;
    category_distribution: Record<string, number>;
    total_reading_tests: number;
    avg_reading_score: number;
    
    // 写作统计
    total_writings: number;
    avg_writing_score: number;
    highest_writing_score: number;
    latest_writing_score: number;
    total_words_written: number;
    
    // 口语统计
    total_speaking_sessions: number;
    avg_speaking_score: number;
    highest_speaking_score: number;
    latest_speaking_score: number;
}

// Reading Test Types
export interface TestQuestion {
    id: number;
    blank_index?: number;  // 完型填空空格序号
    question_text: string;
    options?: string[];  // for cloze
    answer: string;
    explanation: string;
}

export interface TestArticle {
    id: number;
    title: string;
    content: string;
    difficulty_level: string;
}

export interface TestResult {
    score: number;
    total: number;
    percentage: number;
    results: {
        question_id: number;
        user_answer: string;
        correct_answer: string;
        is_correct: boolean;
        explanation: string;
    }[];
}

// Writing Coach Types
export interface WritingTopic {
    id: number;
    title: string;
    description: string;
    category: string;
}

export interface WritingEvaluation {
    ielts: {
        overall: number;
        criteria: {
            task_response: { score: number; comment: string };
            coherence: { score: number; comment: string };
            lexical: { score: number; comment: string };
            grammar: { score: number; comment: string };
        };
    };
    general: {
        overall: number;
        criteria: {
            native_phrasing: { score: number; comment: string };
            grammar_accuracy: { score: number; comment: string };
            spelling: { score: number; comment: string };
        };
    };
    overall_feedback: string;
    improved_version: string;
}

export interface WritingSubmission {
    id: number;
    preview: string;
    topic: string | null;
    score: number;
    created_at: string;
}

// Speaking Coach Types (预留)
export interface SpeakingEvaluation {
    overall_band: number;
    transcription?: string;
    feedback: {
        fluency: { score: number; comment: string };
        vocabulary: { score: number; comment: string };
        grammar: { score: number; comment: string };
    };
    native_suggestion: string;
}

export interface SpeakingSubmission {
    id: number;
    transcription: string;
    overall_band: number;
    fluency_score: number;
    vocabulary_score: number;
    grammar_score: number;
    created_at: string;
}

export type ViewType = 'discover' | 'library' | 'history' | 'vocabulary' | 'stats' | 'test' | 'writing' | 'speaking' | 'vocabulary_test';
