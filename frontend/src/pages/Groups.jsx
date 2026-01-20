import React, { useEffect, useState } from 'react';
import api from '../services/api';
import toast from 'react-hot-toast';
import { Search, Filter, MoreHorizontal, ShieldCheck, ShieldAlert, Trash2, Power } from 'lucide-react';

const Groups = () => {
    const [groups, setGroups] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchGroups();
    }, []);

    const fetchGroups = async () => {
        try {
            const res = await api.get('/api/dashboard/groups');
            setGroups(res.data);
        } catch (error) {
            toast.error("فشل جلب المجموعات");
        } finally {
            setLoading(false);
        }
    };

    const handleToggle = async (groupId) => {
        try {
            const res = await api.post(`/api/dashboard/groups/${groupId}/toggle`);
            if (res.data.status === 'success') {
                toast.success(res.data.new_state ? 'تم تفعيل المجموعة ✅' : 'تم تعطيل المجموعة ⛔');
                setGroups(groups.map(g =>
                    g.id === groupId ? { ...g, settings: { ...g.settings, is_active: res.data.new_state } } : g
                ));
            }
        } catch (error) {
            toast.error('فشل تحديث الحالة');
            console.error(error);
        }
    };

    const handleDelete = async (groupId) => {
        if (!window.confirm("هل أنت متأكد من حذف هذه المجموعة؟ سيتم إزالتها من قاعدة البيانات.")) return;
        try {
            await api.delete(`/api/dashboard/groups/${groupId}`);
            toast.success('تم حذف المجموعة 🗑️');
            setGroups(groups.filter(g => g.id !== groupId));
        } catch (error) {
            toast.error('فشل حذف المجموعة');
            console.error(error);
        }
    };

    if (loading) return <div className="p-10 text-center text-gray-400">جاري التحميل...</div>;

    return (
        <div>
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h2 className="text-2xl font-bold text-gray-800">إدارة المجموعات</h2>
                    <p className="text-gray-500 text-sm">قائمة المجموعات التي يديرها البوت.</p>
                </div>
                <button
                    onClick={fetchGroups}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-lg text-sm font-medium shadow-sm transition-all flex items-center"
                >
                    تحديث القائمة
                </button>
            </div>

            {/* Filters Bar (Future) */}
            <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm mb-6 flex items-center justify-between">
                <div className="relative w-64">
                    <Search className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <input
                        type="text"
                        placeholder="بحث عن مجموعة..."
                        className="w-full pl-4 pr-10 py-2 bg-gray-50 border-none rounded-lg text-sm focus:ring-2 focus:ring-blue-100"
                    />
                </div>
                <div className="flex gap-2">
                    <button className="flex items-center gap-2 px-3 py-2 text-gray-600 hover:bg-gray-50 rounded-lg text-sm transition">
                        <Filter className="w-4 h-4" />
                        <span>تصفية</span>
                    </button>
                </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                <table className="w-full text-right">
                    <thead className="bg-gray-50 text-gray-500 border-b border-gray-100 uppercase text-xs font-semibold">
                        <tr>
                            <th className="p-5 font-medium tracking-wider">اسم المجموعة</th>
                            <th className="p-5 font-medium tracking-wider">المعرف (ID)</th>
                            <th className="p-5 font-medium tracking-wider">الحالة</th>
                            <th className="p-5 font-medium tracking-wider">الإجراءات</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {groups.length === 0 ? (
                            <tr>
                                <td colSpan="4" className="p-10 text-center text-gray-400">
                                    لا توجد مجموعات مسجلة حتى الآن. تأكد من إضافة البوت كمشرف.
                                </td>
                            </tr>
                        ) : (
                            groups.map((group) => (
                                <tr key={group.id} className="hover:bg-blue-50/50 transition-colors duration-150 group">
                                    <td className="p-5 font-medium text-gray-900">{group.title}</td>
                                    <td className="p-5 text-gray-500 text-sm font-mono" dir="ltr">{group.settings?.chat_id || group.id}</td>
                                    <td className="p-5">
                                        <div className="flex items-center gap-2">
                                            {group.settings?.is_active ? (
                                                <ShieldCheck className="w-4 h-4 text-green-600" />
                                            ) : (
                                                <ShieldAlert className="w-4 h-4 text-gray-400" />
                                            )}
                                            <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${group.settings?.is_active
                                                    ? 'bg-green-50 text-green-700 border-green-200'
                                                    : 'bg-gray-100 text-gray-600 border-gray-200'
                                                }`}>
                                                {group.settings?.is_active ? 'نشط' : 'غير نشط'}
                                            </span>
                                        </div>
                                    </td>
                                    <td className="p-5">
                                        <div className="flex items-center gap-2 justify-end">
                                            <button
                                                onClick={() => handleToggle(group.id)}
                                                className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold transition border ${group.settings?.is_active
                                                        ? 'bg-red-50 text-red-600 border-red-100 hover:bg-red-100'
                                                        : 'bg-green-50 text-green-600 border-green-100 hover:bg-green-100'
                                                    }`}
                                            >
                                                <Power className="w-3 h-3" />
                                                {group.settings?.is_active ? "تعطيل" : "تفعيل"}
                                            </button>

                                            <button
                                                onClick={() => handleDelete(group.id)}
                                                className="p-2 rounded-lg text-gray-400 hover:bg-red-50 hover:text-red-600 hover:border-red-100 border border-transparent transition"
                                                title="حذف المجموعة"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default Groups;
