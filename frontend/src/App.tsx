// ============================================================
// CrediShield AI – Root Router Component
// ============================================================

import React from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';

import { useAuth } from '@/context/AuthContext';
import Login from '@/pages/Login';
import Register from '@/pages/Register';
import ApplicantDashboard from '@/pages/ApplicantDashboard';
import OfficerDashboard from '@/pages/OfficerDashboard';
import ApplicationDetail from '@/pages/ApplicationDetail';

// ---- Protected Route Guard ---- //
interface ProtectedRouteProps {
  children: React.ReactNode;
}

function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth();

  // While checking the stored token, show a loader
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="flex flex-col items-center gap-3">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
          <p className="text-sm text-gray-500">Verifying session…</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

// ---- Role-based Dashboard Selector ---- //
function DashboardRouter() {
  const { role } = useAuth();

  if (role === 'loan_officer') {
    return <OfficerDashboard />;
  }
  return <ApplicantDashboard />;
}

// ---- App Routes ---- //
export default function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Protected routes */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardRouter />
          </ProtectedRoute>
        }
      />
      <Route
        path="/applications/:id"
        element={
          <ProtectedRoute>
            <ApplicationDetail />
          </ProtectedRoute>
        }
      />

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
