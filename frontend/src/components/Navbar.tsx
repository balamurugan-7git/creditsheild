// ============================================================
// CrediShield AI – Navbar Component
// Top navigation with branding, user info, and logout
// ============================================================

import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { LogOut, LayoutDashboard, FileText } from 'lucide-react';

import { useAuth } from '@/context/AuthContext';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';

export default function Navbar() {
  const { user, role, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="sticky top-0 z-40 border-b border-gray-200 bg-white shadow-sm">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
        {/* Brand */}
        <Link
          to="/dashboard"
          className="flex items-center gap-2 text-xl font-bold text-gray-900 hover:opacity-80 transition-opacity"
        >
          <span className="text-2xl">🛡️</span>
          <span>
            CrediShield{' '}
            <span className="text-primary-600">AI</span>
          </span>
        </Link>

        {/* Nav links */}
        <nav className="hidden items-center gap-1 md:flex">
          <Link
            to="/dashboard"
            className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-100 hover:text-gray-900"
          >
            <LayoutDashboard size={15} />
            Dashboard
          </Link>
          {role === 'loan_officer' && (
            <Link
              to="/dashboard"
              className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-100 hover:text-gray-900"
            >
              <FileText size={15} />
              Applications
            </Link>
          )}
        </nav>

        {/* Right side: user info + logout */}
        <div className="flex items-center gap-3">
          {user && (
            <div className="hidden flex-col items-end md:flex">
              <span className="text-sm font-medium text-gray-800 leading-none">
                {user.full_name ?? user.email}
              </span>
              <span className="mt-0.5 text-xs text-gray-400">{user.email}</span>
            </div>
          )}

          {/* Role badge */}
          {role && (
            <Badge
              variant={role === 'loan_officer' ? 'primary' : 'default'}
              showIcon={false}
            >
              {role === 'loan_officer' ? 'Loan Officer' : 'Applicant'}
            </Badge>
          )}

          {/* Logout */}
          <Button
            variant="ghost"
            size="sm"
            leftIcon={<LogOut size={15} />}
            onClick={handleLogout}
            title="Sign out"
          >
            <span className="hidden sm:inline">Sign out</span>
          </Button>
        </div>
      </div>
    </header>
  );
}
