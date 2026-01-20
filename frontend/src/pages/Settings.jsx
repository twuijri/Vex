import React, { useState, useEffect } from 'react';
import api from '../services/api';
import toast from 'react-hot-toast';
import { Save, Plus, X, Server, Database, Shield } from 'lucide-react';

const Settings = () => {
    const [config, setConfig] = useState({
        bot_token: '',
        support_group_id: '',
        log_channel_id: '',
        mongo_uri: '',
        telegram_admin_ids: []
    });
    const [newAdminId, setNewAdminId] = useState('');
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        api.get('/api/config/get').then(res => {
            setConfig(res.data);
        }).catch(err => {
            toast.error("فشل تحميل الإعدادات");
        });
    }, []);

    const handleChange = (e) => {
        setConfig({ ...config, [e.target.name]: e.target.value });
    };

    const handleUpdate = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            await api.post('/api/config/update', config);
            toast.success("تم تحديث الإعدادات بنجاح ✅");
        } catch (error) {
            toast.error("فشل تحديث الإعدادات");
        } finally {
            setLoading(false);
        }
    };

    const addAdminId = (e) => {
        e.preventDefault();
        if (!newAdminId) return;
        const id = parseInt(newAdminId.trim());
        if (isNaN(id)) {
            toast.error("الرجاء إدخال رقم صحيح (ID)");
            return;
        }
        if (config.telegram_admin_ids.includes(id)) {
            toast.error("هذا المدير موجود بالفعل");
            return;
        }
        setConfig({ ...config, telegram_admin_ids: [...config.telegram_admin_ids, id] });
        setNewAdminId('');
    };

    const removeAdminId = (idToRemove) => {
        setConfig({
            ...config,
            telegram_admin_ids: config.telegram_admin_ids.filter(id => id !== idToRemove)
        });
    };

    return (
        <div className="max-w-5xl mx-auto pb-10">
            <div className="mb-6">
                <h2 className="text-2xl font-bold text-gray-800">إعدادات النظام</h2>
                <p className="text-gray-500 text-sm">إدارة الاتصال والمدراء.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Column: Form */}
                <div className="lg:col-span-2 space-y-6">
                    <form onSubmit={handleUpdate}>
                        {/* Bot Configuration Card */}
                        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm mb-6">
                            <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                                <Server className="w-5 h-5 text-blue-600" />
                                إعدادات الخادم
                            </h3>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Bot Token</label>
                                    <input
                                        type="text"
                                        name="bot_token"
                                        className="w-full bg-gray-50 border border-gray-300 rounded-lg p-2.5 text-gray-900 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
                                        value={config.bot_token || ''}
                                        placeholder="Enter Bot Token..."
                                        onChange={handleChange}
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">MongoDB URI</label>
                                    <div className="relative">
                                        <Database className="absolute right-3 top-2.5 text-gray-400 w-4 h-4" />
                                        <input
                                            type="text"
                                            name="mongo_uri"
                                            className="w-full bg-gray-50 border border-gray-300 rounded-lg p-2.5 pr-10 text-gray-900 text-sm font-mono focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
                                            value={config.mongo_uri || ''}
                                            placeholder="mongodb://..."
                                            onChange={handleChange}
                                        />
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Support Group ID</label>
                                        <input
                                            type="text"
                                            name="support_group_id"
                                            className="w-full bg-gray-50 border border-gray-300 rounded-lg p-2.5 text-gray-900 text-sm focus:ring-2 focus:ring-blue-500 transition"
                                            value={config.support_group_id || ''}
                                            placeholder="-100..."
                                            onChange={handleChange}
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Log Channel ID</label>
                                        <input
                                            type="text"
                                            name="log_channel_id"
                                            className="w-full bg-gray-50 border border-gray-300 rounded-lg p-2.5 text-gray-900 text-sm focus:ring-2 focus:ring-blue-500 transition"
                                            value={config.log_channel_id || ''}
                                            placeholder="-100..."
                                            onChange={handleChange}
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Save Button */}
                        <div className="flex justify-end">
                            <button
                                type="submit"
                                disabled={loading}
                                className={`flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-xl font-bold text-sm shadow-md hover:shadow-lg transition-all ${loading ? 'opacity-70 cursor-not-allowed' : ''}`}
                            >
                                <Save className="w-4 h-4" />
                                {loading ? 'جاري الحفظ...' : 'حفظ التغييرات'}
                            </button>
                        </div>
                    </form>
                </div>

                {/* Right Column: Admins */}
                <div className="lg:col-span-1">
                    <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm sticky top-24">
                        <h3 className="text-lg font-bold text-gray-800 mb-2 flex items-center gap-2">
                            <Shield className="w-5 h-5 text-purple-600" />
                            مدراء البوت
                        </h3>
                        <p className="text-xs text-gray-500 mb-6">قائمة المعرفات التي تملك صلاحيات التحكم الكامل.</p>

                        <div className="space-y-3 mb-6">
                            {config.telegram_admin_ids && config.telegram_admin_ids.length > 0 ? (
                                config.telegram_admin_ids.map(id => (
                                    <div key={id} className="bg-gray-50 border border-gray-200 rounded-lg p-3 flex justify-between items-center group hover:border-purple-200 hover:bg-purple-50 transition">
                                        <span className="font-mono text-sm text-gray-700">{id}</span>
                                        <button
                                            onClick={() => removeAdminId(id)}
                                            className="text-gray-400 hover:text-red-500 hover:bg-red-50 p-1 rounded transition"
                                        >
                                            <X className="w-4 h-4" />
                                        </button>
                                    </div>
                                ))
                            ) : (
                                <p className="text-center text-gray-400 text-sm py-4">لا يوجد مدراء.</p>
                            )}
                        </div>

                        <div className="flex gap-2">
                            <input
                                type="text"
                                placeholder="ID جديد..."
                                className="bg-gray-50 border border-gray-300 rounded-lg p-2 text-sm flex-1 focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                                value={newAdminId}
                                onChange={(e) => setNewAdminId(e.target.value)}
                            />
                            <button
                                onClick={addAdminId}
                                className="bg-purple-600 hover:bg-purple-700 text-white p-2 rounded-lg transition shadow-sm"
                            >
                                <Plus className="w-5 h-5" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Settings;
