import React from 'react';
import { Outlet } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Sidebar from './Sidebar';
import Topbar from './Topbar';

const Layout = () => {
    return (
        <div className="flex h-screen bg-gray-50 text-gray-900 font-sans" dir="rtl">
            <Toaster position="top-center" toastOptions={{
                style: {
                    background: '#333',
                    color: '#fff',
                },
            }} />

            {/* Sidebar */}
            <Sidebar />

            {/* Main Wrapper */}
            <div className="flex-1 flex flex-col overflow-hidden">
                {/* Header */}
                <Topbar />

                {/* Content */}
                <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50 p-6 md:p-8">
                    <Outlet />
                </main>
            </div>
        </div>
    );
};

export default Layout;
