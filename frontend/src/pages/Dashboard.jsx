import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Users, MessageSquare, ShieldAlert, Activity } from 'lucide-react';

const Dashboard = () => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const res = await api.get('/api/dashboard/stats');
                setStats(res.data);
            } catch (error) {
                console.error("Failed to fetch stats:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchStats();
    }, []);

    if (loading) return <div className="text-center p-10 text-gray-400">جاري التحميل...</div>;

    const StatCard = ({ title, value, icon: Icon, color, bg }) => (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow duration-200">
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="text-gray-500 text-sm font-semibold uppercase tracking-wider">{title}</h3>
                    <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
                </div>
                <div className={`p-4 rounded-full ${bg} ${color}`}>
                    <Icon className="w-6 h-6" />
                </div>
            </div>
            <div className="mt-4 flex items-center text-xs text-gray-400">
                <Activity className="w-3 h-3 mr-1" />
                <span className="mr-1">تحديث مباشر</span>
            </div>
        </div>
    );

    return (
        <div>
            <div className="mb-8">
                <h2 className="text-2xl font-bold text-gray-800">نظرة عامة</h2>
                <p className="text-gray-500 text-sm">أهلاً بك في لوحة تحكم البوت.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <StatCard
                    title="المجموعات النشطة"
                    value={stats?.active_groups || 0}
                    icon={Users}
                    color="text-blue-600"
                    bg="bg-blue-50"
                />
                <StatCard
                    title="الرسائل المعالجة"
                    value={stats?.messages_processed || 0}
                    icon={MessageSquare}
                    color="text-green-600"
                    bg="bg-green-50"
                />
                <StatCard
                    title="المحظورين"
                    value={stats?.bans || 0}
                    icon={ShieldAlert}
                    color="text-red-600"
                    bg="bg-red-50"
                />
            </div>

            <div className="mt-10 bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
                <h3 className="text-lg font-bold text-gray-800 mb-4 px-2 border-r-4 border-blue-500">📢 سجل النشاطات (Live Activity)</h3>
                <div className="text-center py-10">
                    <div className="bg-gray-50 inline-block p-4 rounded-full mb-3">
                        <Activity className="w-8 h-8 text-gray-300" />
                    </div>
                    <p className="text-gray-400 text-sm">جاري تسجيل العمليات الجديدة...</p>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
