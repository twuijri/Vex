import axios from 'axios';

// ==============================================================================
// 📄 File: frontend/src/services/api.js
// 📝 Description: Axios instance for API interactions.
// 📝 الوصف: إعداد Axios للتفاعل مع الواجهة الخلفية.
// ==============================================================================

const API_URL = import.meta.env.VITE_API_URL || "";

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Interceptor to add Token if exists (Setup doesn't need it)
// معترض لإضافة التوكن إذا وجد (الإعداد لا يحتاجه)
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export default api;
