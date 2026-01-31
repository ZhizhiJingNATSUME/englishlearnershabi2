import type { Article, ArticleAnalysis, ReadingHistory, User, UserStats, VocabularyItem, LearningWord, VocabularyQuizQuestion, DiscoverStats, TestQuestion, TestArticle, TestResult, EnglishPilotScenario, EnglishPilotResponse, EnglishPilotMessage } from '../types';

export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:5000/api';

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

export const discoverArticles = async (data: {
    user_id: number;
    categories: string[];
    sources?: string[];
    count?: number;
    language?: string;
}): Promise<{ stats: DiscoverStats; recommendations: Article[] }> => {
    return handleResponse(await fetch(`${API_BASE}/discover`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    }));
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

// Like/Unlike article
export const likeArticle = async (userId: number, articleId: number, liked: number): Promise<{ message: string }> => {
    return handleResponse(await fetch(`${API_BASE}/reading_history`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: userId,
            article_id: articleId,
            liked: liked, // 1 for like, -1 for dislike, 0 for neutral
            completion_rate: 1.0
        }),
    }));
};

// Get user profile (interests, embedding status, etc.)
export const getUserProfile = async (userId: number): Promise<any> => {
    return handleResponse(await fetch(`${API_BASE}/users/${userId}/profile`));
};

// Refresh user profile/embedding
export const refreshUserProfile = async (userId: number): Promise<{ message: string }> => {
    return handleResponse(await fetch(`${API_BASE}/users/${userId}/refresh_profile`, {
        method: 'POST',
    }));
};

export const chatEnglishPilot = async (data: {
    user_id: number;
    scenario: EnglishPilotScenario;
    level: string;
    messages: EnglishPilotMessage[];
}): Promise<EnglishPilotResponse> => {
    return handleResponse(await fetch(`${API_BASE}/english_pilot/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    }));
};

export const transcribeEnglishPilotAudio = async (audio: Blob): Promise<{ transcription: string }> => {
    const extension = audio.type.includes('mp4')
        ? 'mp4'
        : audio.type.includes('ogg')
            ? 'ogg'
            : 'webm';
    const formData = new FormData();
    formData.append('audio', audio, `english-pilot.${extension}`);
    return handleResponse(await fetch(`${API_BASE}/english_pilot/stt`, {
        method: 'POST',
        body: formData,
    }));
};

export const translateArticleSegment = async (data: {
    text: string;
    target_language?: string;
}): Promise<{ translation: string }> => {
    const response = await fetch(`${API_BASE}/translate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });
    if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Network response was not ok' }));
        const message = error.error || error.message || 'API request failed';
        const err = new Error(message) as Error & { status?: number; detail?: string };
        err.status = response.status;
        err.detail = error.detail;
        throw err;
    }
    return response.json();
};
