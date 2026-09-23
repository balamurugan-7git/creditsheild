// ============================================================
// CrediShield AI – Loan Officer Dashboard
// Portfolio-grade risk review portal for credit underwriters
// ============================================================

import React, { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useApplications } from '@/hooks/usePrediction';
import Navbar from '@/components/Navbar';
import ApplicationTable from '@/components/ApplicationTable';
import type { DecisionType } from '@/types';
import {
  FileCheck2,
  Clock,
  CheckCircle2,
  XCircle,
  TrendingUp,
  Filter,
} from 'lucide-react';

export default function OfficerDashboard() {
  const { user } = useAuth();
  const [page, setPage] = useState(0);
  const pageSize = 20;
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const { data: appData, isLoading } = useApplications(page * pageSize, pageSize);

  const applications = appData?.applications || [];
  const total = appData?.total || applications.length;

  // Filter applications in-memory if needed
  const filteredApps = applications.filter((app) => {
    if (statusFilter === 'all') return true;
    const effectiveDecision = app.officer_override || app.decision;
    return effectiveDecision === statusFilter;
  });

  // Calculate quick metrics
  const totalApproved = applications.filter(
    (a) => (a.officer_override || a.decision) === 'approved'
  ).length;
  const totalReview = applications.filter(
    (a) => !a.officer_override && a.decision === 'manual_review'
  ).length;
  const totalRejected = applications.filter(
    (a) => (a.officer_override || a.decision) === 'rejected'
  ).length;
  const totalOverrides = applications.filter((a) => a.officer_override !== null).length;

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-slate-900">
            Loan Underwriting & Risk Queue
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Review applicant risk distributions, evaluate SHAP feature attributions, and manage decision overrides.
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="bg-white p-5 rounded-xl border border-slate-100 shadow-sm flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
              <FileCheck2 className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Scored</p>
              <h3 className="text-2xl font-bold text-slate-900">{total}</h3>
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-100 shadow-sm flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center shrink-0">
              <Clock className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Manual Review</p>
              <h3 className="text-2xl font-bold text-slate-900">{totalReview}</h3>
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-100 shadow-sm flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-green-50 text-green-600 flex items-center justify-center shrink-0">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Approved Loans</p>
              <h3 className="text-2xl font-bold text-slate-900">{totalApproved}</h3>
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-100 shadow-sm flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center shrink-0">
              <TrendingUp className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Officer Overrides</p>
              <h3 className="text-2xl font-bold text-slate-900">{totalOverrides}</h3>
            </div>
          </div>
        </div>

        {/* Filter and Table Card */}
        <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-100 mb-6">
            <div>
              <h2 className="text-lg font-bold text-slate-900">Application Queue</h2>
              <p className="text-xs text-slate-500">
                Sorted by latest submission. Click view to inspect SHAP explanations and apply overrides.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <Filter className="w-4 h-4 text-slate-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="text-sm rounded-lg border border-slate-300 py-1.5 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Statuses</option>
                <option value="manual_review">Manual Review Only</option>
                <option value="approved">Approved Only</option>
                <option value="rejected">Rejected Only</option>
              </select>
            </div>
          </div>

          <ApplicationTable
            applications={filteredApps}
            total={filteredApps.length}
            page={page}
            pageSize={pageSize}
            isLoading={isLoading}
            onPageChange={setPage}
            filterLabel={statusFilter !== 'all' ? statusFilter : undefined}
          />
        </div>
      </main>
    </div>
  );
}
