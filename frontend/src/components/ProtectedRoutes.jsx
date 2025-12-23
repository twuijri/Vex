import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';

// ==============================================================================
// 📄 File: frontend/src/components/ProtectedRoutes.jsx
// 📝 Description: Wrapper to protect routes requiring authentication.
// 📝 الوصف: مكون لحماية المسارات التي تتطلب تسجيل دخول.
// ==============================================================================

const ProtectedRoutes = () => {
    const token = localStorage.getItem('token');

    // Simple check: exists?
    // TODO: Verify validity with backend if needed.
    // فحص بسيط: هل التوكن موجود؟
    return token ? <Outlet /> : <Navigate to="/login" replace />;
};

export default ProtectedRoutes;
