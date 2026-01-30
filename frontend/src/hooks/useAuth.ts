// src/hooks/useAuth.ts
import { useState, useEffect } from 'react';
import type { User } from '../types';
import * as api from '../services/api';

export const useAuth = () => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const savedUser = localStorage.getItem('faga_user');
        if (savedUser) {
            setUser(JSON.parse(savedUser));
        }
        setLoading(false);
    }, []);

    const login = async (username: string) => {
        try {
            const response = await api.login(username);
            const userData = response.user;
            setUser(userData);
            localStorage.setItem('faga_user', JSON.stringify(userData));
            return userData;
        } catch (error) {
            console.error('Login failed:', error);
            throw error;
        }
    };

    const register = async (username: string, level: string) => {
        try {
            const response = await api.register({ username, english_level: level });
            const userData = response.user;
            setUser(userData);
            localStorage.setItem('faga_user', JSON.stringify(userData));
            return userData;
        } catch (error) {
            console.error('Registration failed:', error);
            throw error;
        }
    };

    const logout = () => {
        setUser(null);
        localStorage.removeItem('faga_user');
    };

    return { user, loading, login, register, logout };
};
