// ============================================================
// CrediShield AI – Applicant Dashboard
// ============================================================

import React, { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useApplications, usePrediction } from '@/hooks/usePrediction';
import Navbar from '@/components/Navbar';
import ApplicationForm from '@/components/ApplicationForm';
import RiskResultCard from '@/components/RiskResultCard';
import ApplicationTable from '@/components/ApplicationTable';
import type { Application, LoanApplicationInput } from '@/types';
import { FileText, PlusCircle, CheckCircle2, Clock, AlertCircle } from 'lucide-react';

export default function ApplicantDashboard() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'apply' | 'history'>('apply');
  const [lastScoredApp, setLastScoredApp] = useState<Application | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [formKey, setFormKey] = useState<number>(0);

  const { data: appData, isLoading: isLoadingApps, refetch } = useApplications(0, 20);
  const { mutate: scoreApplication, isLoading: isPending } = usePrediction();

  const handleNewApplication = () => {
    setActiveTab('apply');
    setLastScoredApp(null);
    setErrorMsg(null);
    setFormKey((k) => k + 1);
  };

  const handleFormSubmit = (data: LoanApplicationInput) => {
    setErrorMsg(null);
    scoreApplication(data, {
      onSuccess: (result) => {
        setLastScoredApp(result);
        setErrorMsg(null);
        refetch();
      },
      onError: (err: any) => {
        const detail = err.response?.data?.detail;
        const message = typeof detail === 'string' ? detail : (err.message || 'Failed to score application. Please check backend status.');
        setErrorMsg(message);
      },
    });
  };

  const applications = appData?.applications || [];

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">
              Welcome back, {user?.full_name || user?.email.split('@')[0]}
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              Apply for a loan with instant, transparent AI-driven credit scoring.
            </p>
          </div>

          <div className="flex items-center gap-2 bg-white p-1 rounded-xl border border-slate-200 shadow-sm">
            <button
              onClick={handleNewApplication}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                activeTab === 'apply'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <PlusCircle className="w-4 h-4" /> New Application
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                activeTab === 'history'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <FileText className="w-4 h-4" /> My Applications ({applications.length})
            </button>
          </div>
        </div>

        {/* Tab 1: Apply */}
        {activeTab === 'apply' && (
          <div className="space-y-8">
            {errorMsg && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl flex items-center gap-3">
                <AlertCircle className="w-5 h-5 flex-shrink-0 text-red-500" />
                <div className="text-sm font-medium">{errorMsg}</div>
              </div>
            )}

            {lastScoredApp && (
              <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2 text-green-600 font-semibold text-sm">
                    <CheckCircle2 className="w-5 h-5" /> Evaluation Complete
                  </div>
                  <button
                    onClick={handleNewApplication}
                    className="text-xs font-semibold text-blue-600 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5"
                  >
                    <PlusCircle className="w-3.5 h-3.5" /> Start New Application
                  </button>
                </div>
                <RiskResultCard application={lastScoredApp} />
              </div>
            )}

            <ApplicationForm key={formKey} onSubmit={handleFormSubmit} isLoading={isPending} />
          </div>
        )}

        {/* Tab 2: History */}
        {activeTab === 'history' && (
          <div className="space-y-4">
            <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
              <h2 className="text-lg font-bold text-slate-900 mb-4">Application History</h2>
              <ApplicationTable
                applications={applications}
                total={appData?.total ?? applications.length}
                page={0}
                onPageChange={() => {}}
                isLoading={isLoadingApps}
              />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
