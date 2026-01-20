import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Setup from './pages/Setup';
import Login from './pages/Login';

import ProtectedRoutes from './components/ProtectedRoutes';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Groups from './pages/Groups';
import Settings from './pages/Settings';



function App() {
  return (
    <Router>
      <Routes>
        <Route path="/setup" element={<Setup />} />
        <Route path="/login" element={<Login />} />

        {/* Protected Dashboard Routes */}
        <Route element={<ProtectedRoutes />}>
          <Route element={<Layout />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/dashboard/groups" element={<Groups />} />
            <Route path="/dashboard/settings" element={<Settings />} />


          </Route>
        </Route>

        {/* Default Redirect: Check Auth or Setup later */}

        <Route path="*" element={<Navigate to="/setup" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
