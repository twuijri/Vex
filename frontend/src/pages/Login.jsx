import React, { useState } from 'react';
import api from '../services/api';
import toast, { Toaster } from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';

// ==============================================================================
// 📄 File: frontend/src/pages/Login.jsx
// 📝 Description: Admin Login Page.
// 📝 الوصف: صفحة تسجيل دخول المدير.
// ==============================================================================

const Login = () => {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState({
        username: '',
        password: ''
    });

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            // OAuth2PasswordRequestForm expects form-data usually, but FastAPI handles JSON too if configured,
            // standard OAuth2 expects x-www-form-urlencoded.
            // Let's send as form data for compatibility with FastAPI's OAuth2PasswordRequestForm
            const params = new URLSearchParams();
            params.append('username', formData.username);
            params.append('password', formData.password);

            const res = await api.post('/api/login', params, {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
            });

            // Save Token
            localStorage.setItem('token', res.data.access_token);
            toast.success('تم تسجل الدخول بنجاح');

            setTimeout(() => {
                navigate('/dashboard');
            }, 1000);

        } catch (error) {
            console.error(error);
            toast.error(error.response?.data?.detail || "خطأ في اسم المستخدم أو كلمة المرور");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
            <Toaster position="top-center" />
            <div className="bg-gray-800 p-8 rounded-lg shadow-2xl w-full max-w-sm border border-gray-700">
                <h2 className="text-2xl font-bold mb-6 text-center text-white">
                    🔐 تسجيل الدخول
                </h2>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-gray-300 text-sm font-medium mb-1">اسم المستخدم</label>
                        <input
                            type="text"
                            name="username"
                            required
                            className="w-full bg-gray-700 text-white border border-gray-600 rounded p-2 focus:ring-2 focus:ring-blue-500 outline-none"
                            value={formData.username}
                            onChange={handleChange}
                        />
                    </div>
                    <div>
                        <label className="block text-gray-300 text-sm font-medium mb-1">كلمة المرور</label>
                        <input
                            type="password"
                            name="password"
                            required
                            className="w-full bg-gray-700 text-white border border-gray-600 rounded p-2 focus:ring-2 focus:ring-blue-500 outline-none"
                            value={formData.password}
                            onChange={handleChange}
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className={`w-full bg-green-600 hover:bg-green-700 text-white font-bold py-2 rounded transition ${loading ? 'opacity-50' : ''}`}
                    >
                        {loading ? 'جاري التحقق...' : 'دخول'}
                    </button>
                </form>
            </div>
        </div>
    );
};

export default Login;
