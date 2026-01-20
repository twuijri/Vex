import React, { useState, useEffect } from 'react';
import api from '../services/api';
import toast, { Toaster } from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';

// ==============================================================================
// 📄 File: frontend/src/pages/Setup.jsx
// 📝 Description: Initial Setup Wizard Page (Simplified).
// 📝 الوصف: صفحة معالج الإعداد الأولي (مبسطة حسب طلب المستخدم).
// ==============================================================================

const Setup = () => {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState({
        admin_username: '',
        admin_password_hash: '',
        mongo_uri: 'mongodb://mongodb:27017',
        bot_token: '',  // Still required for initial boot
        // support_group_id & log_channel_id removed for simplicity, accessible later in Settings
    });

    useEffect(() => {
        api.get('/api/status').then(res => {
            if (res.data.setup_complete) {
                navigate('/dashboard');
            }
        }).catch(err => {
            console.error("Status Check Failed:", err);
        });
    }, []);

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            await api.post('/api/setup', formData);
            toast.success('تم الإعداد بنجاح! سيتم توجيهك...');
            setTimeout(() => {
                navigate('/login');
            }, 2000);
        } catch (error) {
            toast.error(error.response?.data?.detail || "حدث خطأ أثناء الإعداد");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center p-4">
            <Toaster position="top-center" />
            <div className="bg-gray-800 p-8 rounded-lg shadow-2xl w-full max-w-lg border border-gray-700">
                <h1 className="text-3xl font-bold mb-6 text-center text-blue-500">
                    🪄 إعداد بوتر 2025
                </h1>
                <p className="text-gray-400 text-center mb-8">
                    مرحباً! دعنا نضبط الإعدادات الأساسية للنظام.
                </p>

                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Admin Credentials */}
                    <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium mb-1">اسم المستخدم (Admin)</label>
                                <input
                                    type="text"
                                    name="admin_username"
                                    required
                                    className="w-full bg-gray-700 border border-gray-600 rounded p-2 focus:ring-2 focus:ring-blue-500 outline-none"
                                    value={formData.admin_username}
                                    onChange={handleChange}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-1">كلمة المرور</label>
                                <input
                                    type="password"
                                    name="admin_password_hash"
                                    required
                                    className="w-full bg-gray-700 border border-gray-600 rounded p-2 focus:ring-2 focus:ring-blue-500 outline-none"
                                    value={formData.admin_password_hash}
                                    onChange={handleChange}
                                />
                            </div>
                        </div>
                    </div>

                    <hr className="border-gray-700" />

                    {/* Database */}
                    <div>
                        <label className="block text-sm font-medium mb-1">رابط قاعدة البيانات (MongoDB URI)</label>
                        <input
                            type="text"
                            name="mongo_uri"
                            placeholder="mongodb://mongodb:27017"
                            required
                            className="w-full bg-gray-700 border border-gray-600 rounded p-2 focus:ring-2 focus:ring-blue-500 outline-none"
                            value={formData.mongo_uri}
                            onChange={handleChange}
                        />
                        <p className="text-xs text-gray-500 mt-1">
                            للاستخدام المحلي: <code>mongodb://mongodb:27017</code>
                        </p>
                    </div>

                    {/* Bot Token - Critical */}
                    <div>
                        <label className="block text-sm font-medium mb-1">توكن البوت (Bot Token)</label>
                        <input
                            type="text"
                            name="bot_token"
                            placeholder="123456789:ABCdefGHIjklMNOpqrs..."
                            required
                            className="w-full bg-gray-700 border border-gray-600 rounded p-2 focus:ring-2 focus:ring-blue-500 outline-none"
                            value={formData.bot_token}
                            onChange={handleChange}
                        />
                        <p className="text-xs text-gray-500 mt-1">
                            مطلوب لتشغيل البوت لأول مرة.
                        </p>
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className={`w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded transition ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                        {loading ? 'جاري الحفظ...' : 'حفظ وبدء التشغيل 🚀'}
                    </button>
                </form>
            </div>
        </div>
    );
};

export default Setup;
