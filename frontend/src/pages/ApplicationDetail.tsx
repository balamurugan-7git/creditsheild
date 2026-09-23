// ============================================================
// CrediShield AI – Application Detail Page
// Full inspection of single application, SHAP attributions & override
// ============================================================

import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { useApplication, useOverrideApplication } from '@/hooks/usePrediction';
import Navbar from '@/components/Navbar';
import RiskResultCard from '@/components/RiskResultCard';
import OverrideModal from '@/components/OverrideModal';
import Button from '@/components/ui/Button';
import {
  ArrowLeft,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  History,
  FileSpreadsheet,
} from 'lucide-react';

export default function ApplicationDetail() {
  const { id } = useParams<{ id: string }>();
  const applicationId = Number(id);
  const navigate = useNavigate();
  const { role } = useAuth();
  const [isOverrideOpen, setIsOverrideOpen] = useState(false);

  const { data: application, isLoading, error } = useApplication(applicationId);
  const { mutate: performOverride, isLoading: isOverriding } = useOverrideApplication(applicationId);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col">
        <Navbar />
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <div className="h-10 w-10 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600" />
            <p className="text-sm text-slate-500">Loading application details…</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !application) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col">
        <Navbar />
        <div className="flex-1 flex flex-col items-center justify-center p-4">
          <ShieldAlert className="w-12 h-12 text-red-500 mb-3" />
          <h2 className="text-lg font-bold text-slate-900">Application Not Found</h2>
          <p className="text-sm text-slate-500 mb-4">
            Could not retrieve application #{applicationId} or you do not have permission.
          </p>
          <Button variant="secondary" onClick={() => navigate('/dashboard')}>
            Return to Dashboard
          </Button>
        </div>
      </div>
    );
  }

  const handleOverrideSubmit = (data: { decision: 'approved' | 'rejected'; reason: string }) => {
    performOverride(data, {
      onSuccess: () => {
        setIsOverrideOpen(false);
      },
    });
  };

  const isOfficer = role === 'loan_officer';

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/dashboard')}
              className="p-2 bg-white rounded-lg border border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">
                Application #{application.id}
              </h1>
              <p className="text-xs text-slate-500">
                Applicant ID: {application.applicant_id} • Scored on{' '}
                {new Date(application.scored_at).toLocaleString()}
              </p>
            </div>
          </div>

          {/* Officer override action */}
          {isOfficer && (
            <Button
              variant="secondary"
              onClick={() => setIsOverrideOpen(true)}
              className="flex items-center gap-2"
            >
              <AlertTriangle className="w-4 h-4 text-amber-500" />
              Manual Decision Override
            </Button>
          )}
        </div>

        {/* Audit Override Banner if exists */}
        {application.officer_override && (
          <div className="mb-6 p-4 rounded-xl border border-purple-200 bg-purple-50 flex items-start gap-3">
            <History className="w-5 h-5 text-purple-600 mt-0.5 shrink-0" />
            <div>
              <h4 className="text-sm font-bold text-purple-900">
                Loan Officer Override Applied ({application.officer_override.toUpperCase()})
              </h4>
              <p className="text-xs text-purple-700 mt-0.5">
                Officer ID #{application.override_by} on{' '}
                {application.override_at && new Date(application.override_at).toLocaleString()}
              </p>
              <p className="text-sm text-purple-900 mt-2 bg-white/70 p-3 rounded-lg border border-purple-100 italic">
                "{application.override_reason}"
              </p>
            </div>
          </div>
        )}

        {/* Risk Result Card (Gauge + SHAP) */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6 mb-8">
          <RiskResultCard application={application} />
        </div>

        {/* Input Features Summary Table */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
          <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-100">
            <FileSpreadsheet className="w-5 h-5 text-blue-600" />
            <h3 className="text-base font-bold text-slate-900">Application Feature Payload</h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 text-sm">
            {Object.entries(application.input_features || {}).map(([key, value]) => (
              <div key={key} className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                <span className="text-xs font-semibold text-slate-500 uppercase block tracking-wider truncate" title={key}>
                  {key}
                </span>
                <span className="text-sm font-medium text-slate-900 mt-1 block">
                  {value !== null && value !== undefined ? String(value) : '—'}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Override Modal */}
        {isOfficer && (
          <OverrideModal
            isOpen={isOverrideOpen}
            onClose={() => setIsOverrideOpen(false)}
            onSubmit={handleOverrideSubmit}
            currentDecision={application.decision}
            probability={application.probability}
            isLoading={isOverriding}
          />
        )}
      </main>
    </div>
  );
}
