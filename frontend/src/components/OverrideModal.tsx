// ============================================================
// CrediShield AI – Loan Officer Override Modal
// Allows loan officers to manually override AI decisions with audit reason
// ============================================================

import React, { useState } from 'react';
import { AlertCircle, CheckCircle, X } from 'lucide-react';
import type { DecisionType, OverrideRequest } from '@/types';
import Button from './ui/Button';

interface OverrideModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: OverrideRequest) => void;
  currentDecision: DecisionType;
  probability: number;
  isLoading?: boolean;
}

export default function OverrideModal({
  isOpen,
  onClose,
  onSubmit,
  currentDecision,
  probability,
  isLoading = false,
}: OverrideModalProps) {
  const [decision, setDecision] = useState<'approved' | 'rejected'>('approved');
  const [reason, setReason] = useState('');
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (reason.trim().length < 10) {
      setError('A detailed reason code of at least 10 characters is required for auditing purposes.');
      return;
    }
    setError(null);
    onSubmit({ decision, reason: reason.trim() });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/50 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white rounded-xl max-w-lg w-full p-6 shadow-xl border border-gray-100">
        <div className="flex items-center justify-between pb-4 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-amber-500" />
            <h3 className="text-lg font-bold text-gray-900">Manual Decision Override</h3>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 rounded-lg p-1 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-600 flex justify-between items-center">
            <span>
              AI Recommended Decision: <strong className="uppercase text-gray-900">{currentDecision}</strong>
            </span>
            <span>
              Risk Probability: <strong className="text-gray-900">{(probability * 100).toFixed(1)}%</strong>
            </span>
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-800 mb-2">Override Decision</label>
            <div className="grid grid-cols-2 gap-3">
              <label
                className={`flex items-center justify-center gap-2 p-3 rounded-lg border cursor-pointer font-medium text-sm transition-all ${
                  decision === 'approved'
                    ? 'border-green-500 bg-green-50 text-green-700 font-semibold'
                    : 'border-gray-200 text-gray-700 hover:border-gray-300'
                }`}
              >
                <input
                  type="radio"
                  name="override_decision"
                  value="approved"
                  checked={decision === 'approved'}
                  onChange={() => setDecision('approved')}
                  className="sr-only"
                />
                <CheckCircle className="w-4 h-4" /> Approve Loan
              </label>

              <label
                className={`flex items-center justify-center gap-2 p-3 rounded-lg border cursor-pointer font-medium text-sm transition-all ${
                  decision === 'rejected'
                    ? 'border-red-500 bg-red-50 text-red-700 font-semibold'
                    : 'border-gray-200 text-gray-700 hover:border-gray-300'
                }`}
              >
                <input
                  type="radio"
                  name="override_decision"
                  value="rejected"
                  checked={decision === 'rejected'}
                  onChange={() => setDecision('rejected')}
                  className="sr-only"
                />
                <AlertCircle className="w-4 h-4" /> Reject Loan
              </label>
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-800 mb-1">
              Required Reason / Regulatory Justification
            </label>
            <textarea
              rows={4}
              value={reason}
              onChange={(e) => {
                setReason(e.target.value);
                if (error) setError(null);
              }}
              placeholder="e.g. Additional co-signor provided, verified secondary stable rental income not captured in application, or policy exception approved by credit committee."
              className="w-full text-sm rounded-lg border border-gray-300 p-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {error && <p className="text-red-500 text-xs mt-1">{error}</p>}
            <p className="text-gray-400 text-xs mt-1">
              This reason is immutably logged into the PostgreSQL audit table along with your officer ID.
            </p>
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-gray-100">
            <Button type="button" variant="secondary" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={isLoading}>
              Commit Override
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
