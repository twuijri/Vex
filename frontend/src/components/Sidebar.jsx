import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Home, Users, Settings, LogOut, LayoutDashboard } from 'lucide-react';

const Sidebar = () => {
    const location = useLocation();
    const navigate = useNavigate();

    const handleLogout = () => {
        localStorage.removeItem('token');
        navigate('/login');
    };

    const navItems = [
        { path: '/dashboard', label: 'الإحصائيات', icon: LayoutDashboard },
        { path: '/dashboard/groups', label: 'المجموعات', icon: Users },
        { path: '/dashboard/settings', label: 'الإعدادات', icon: Settings },
    ];

    return (
        <div className="w-64 bg-white border-l border-gray-200 flex flex-col h-screen shadow-lg z-10 sticky top-0">
            {/* Logo Area */}
            <div className="p-6 border-b border-gray-100 flex items-center space-x-3 space-x-reverse">
                <div className="w-12 h-12 flex items-center justify-center shrink-0">
                    <img src="/logo.png" alt="Bot Logo" className="w-full h-full object-cover rounded-full shadow-md hover:scale-105 transition-transform" />
                </div>
                <div>
                    <h1 className="text-xl font-bold text-gray-800 tracking-tight">Vex</h1>
                    {/* <p className="text-xs text-gray-500 font-medium">Google Style Admin</p> */}
                </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
                {navItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = location.pathname === item.path;
                    return (
                        <Link
                            key={item.path}
                            to={item.path}
                            className={`flex items-center space-x-3 space-x-reverse px-4 py-3 rounded-lg transition-all duration-200 group
                                ${isActive
                                    ? 'bg-blue-50 text-blue-700 font-semibold shadow-sm ring-1 ring-blue-100'
                                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                                }`}
                        >
                            <Icon className={`w-5 h-5 ${isActive ? 'text-blue-600' : 'text-gray-400 group-hover:text-gray-600'}`} />
                            <span>{item.label}</span>
                        </Link>
                    );
                })}
            </nav>

            {/* Logout & Attribution */}
            <div className="p-4 border-t border-gray-100 bg-gray-50">
                <button
                    onClick={handleLogout}
                    className="flex items-center w-full px-4 py-3 text-red-600 rounded-lg hover:bg-red-50 hover:shadow-sm transition-all duration-200 mb-4"
                >
                    <LogOut className="w-5 h-5 ml-3" />
                    <span className="font-medium">تسجيل الخروج</span>
                </button>

                <div className="text-center pt-2 border-t border-gray-200">
                    <p className="text-xs text-gray-400">Developed by</p>
                    <a
                        href="https://github.com/twuijri"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs font-bold text-gray-600 hover:text-blue-600 transition"
                    >
                        @twuijri
                    </a>
                </div>
            </div>
        </div>
    );
};

export default Sidebar;
