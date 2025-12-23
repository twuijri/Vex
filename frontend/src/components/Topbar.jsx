import React from 'react';
import { Bell, Search, User } from 'lucide-react';

const Topbar = () => {
    return (
        <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-8 sticky top-0 z-10 shadow-sm">
            {/* Search / Breadcrumbs */}
            <div className="flex items-center w-1/3">
                <div className="relative w-full max-w-md">
                    <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <input
                        type="text"
                        placeholder="بحث في المجموعات..."
                        className="w-full pl-4 pr-10 py-2 bg-gray-100 border-none rounded-full text-sm focus:ring-2 focus:ring-blue-100 focus:bg-white transition-all text-right"
                    />
                </div>
            </div>

            {/* Right Side Actions */}
            <div className="flex items-center space-x-4 space-x-reverse">
                <button className="p-2 text-gray-400 hover:bg-gray-100 rounded-full transition relative">
                    <Bell className="w-5 h-5" />
                    <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border border-white"></span>
                </button>

                <div className="flex items-center space-x-3 space-x-reverse pl-4 border-l border-gray-200">
                    <div className="text-right hidden md:block">
                        <p className="text-sm font-semibold text-gray-700">المشرف العام</p>
                        <p className="text-xs text-gray-500">Admin</p>
                    </div>
                    <div className="w-9 h-9 bg-gradient-to-tr from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white font-bold shadow-md ring-2 ring-white">
                        A
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Topbar;
