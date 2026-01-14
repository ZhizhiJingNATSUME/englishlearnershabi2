import type { Article, ArticleAnalysis, ReadingHistory, User, UserStats, VocabularyItem, LearningWord, VocabularyQuizQuestion, TestQuestion, TestArticle, TestResult } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:5000/api';

const handleResponse = async (response: Response) => {
    if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Network response was not ok' }));
        throw new Error(error.error || error.message || 'API request failed');
    }
    return response.json();
};

// User related
export const login = async (username: string): Promise<{ user: User; message: string }> => {
    return handleResponse(await fetch(`${API_BASE}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username }),
    }));
};

export const register = async (userData: Partial<User>): Promise<{ user: User; message: string }> => {
    return handleResponse(await fetch(`${API_BASE}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData),
    }));
};

export const getUserProfiles = async (username: string): Promise<User[]> => {
    return handleResponse(await fetch(`${API_BASE}/users?username=${username}`));
};

// Article related
export const getArticles = async (category?: string, level?: string): Promise<{ articles: Article[] }> => {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (level) params.append('level', level);
    return handleResponse(await fetch(`${API_BASE}/articles?${params.toString()}`));
};

export const getArticle = async (id: number): Promise<Article> => {
    return handleResponse(await fetch(`${API_BASE}/articles/${id}`));
};

export const getArticleAnalysis = async (id: number): Promise<ArticleAnalysis> => {
    return handleResponse(await fetch(`${API_BASE}/articles/${id}/analysis`));
};

export const getRecommendations = async (userId: number, limit = 10): Promise<{ recommendations: Article[] }> => {
    return handleResponse(await fetch(`${API_BASE}/recommend?user_id=${userId}&limit=${limit}`));
};

// History
export const saveReadingHistory = async (data: { user_id: number; article_id: number; completion_rate: number; time_spent: number }) => {
    return handleResponse(await fetch(`${API_BASE}/reading_history`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    }));
};

export const getReadingHistory = async (userId: number): Promise<{ history: ReadingHistory[] }> => {
    return handleResponse(await fetch(`${API_BASE}/reading_history/${userId}`));
};

// Vocabulary
export const addVocabulary = async (data: {
    user_id: number;
    word: string;
    article_id?: number;
    source_article_id?: number;
    definition?: string;
    translation?: string;
    example_sentence?: string;
    example_translation?: string;
}) => {
    return handleResponse(await fetch(`${API_BASE}/vocabulary`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    }));
};

export const getVocabulary = async (userId: number): Promise<{ vocabulary: VocabularyItem[] }> => {
    return handleResponse(await fetch(`${API_BASE}/vocabulary/${userId}`));
};

export const getLearningWord = async (listName?: string): Promise<LearningWord> => {
    const params = new URLSearchParams();
    if (listName) params.append('list_name', listName);
    const query = params.toString();
    return handleResponse(await fetch(`${API_BASE}/vocabulary/learn${query ? `?${query}` : ''}`));
};

export const getVocabularyQuiz = async (userId: number): Promise<VocabularyQuizQuestion> => {
    return handleResponse(await fetch(`${API_BASE}/vocabulary/quiz/${userId}`));
};

// Stats
export const getUserStats = async (userId: number): Promise<UserStats> => {
    return handleResponse(await fetch(`${API_BASE}/stats/${userId}`));
};

// Reading Test
export const getTestArticles = async (level: string = 'B1', limit: number = 10): Promise<{ articles: Article[] }> => {
    return handleResponse(await fetch(`${API_BASE}/reading_test/articles?level=${level}&limit=${limit}`));
};

export const generateTest = async (data: { article_id: number; question_type: 'cloze' | 'true_false'; num_questions: number }): Promise<{ article: TestArticle; questions: TestQuestion[]; question_type: string }> => {
    return handleResponse(await fetch(`${API_BASE}/reading_test/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    }));
};

export const submitTest = async (data: { user_id: number; article_id: number; answers: any[]; questions: TestQuestion[] }): Promise<TestResult> => {
    return handleResponse(await fetch(`${API_BASE}/reading_test/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    }));
};

// Writing Evaluation (placeholder)
export const evaluateWriting = async (data: { text: string; topic?: string }): Promise<any> => {
    return handleResponse(await fetch(`${API_BASE}/writing/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    }));
};
