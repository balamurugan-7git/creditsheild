// ============================================================
// CrediShield AI – Application Table Component
// Paginated list of applications with skeleton, empty state
// ============================================================

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { format, parseISO } from 'date-fns';
import { ChevronLeft, ChevronRight, Eye, Inbox } from 'lucide-react';

import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import type { Application, DecisionType } from '@/types';

// ---- Skeleton row ---- //
function SkeletonRow() {
  return (
    <tr className="animate-pulse">
      {Array.from({ length: 6 }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <div className="h-4 rounded bg-gray-200" style={{ width: `${60 + i * 5}%` }} />
        </td>
      ))}
    </tr>
  );
}

// ---- Props ---- //
interface ApplicationTableProps {
  applications: Application[];
  total: number;
  page: number;
  pageSize?: number;
  isLoading?: boolean;
  onPageChange: (page: number) => void;
  /** Optional filter currently applied (for display) */
  filterLabel?: string;
}

export default function ApplicationTable({
  applications,
  total,
  page,
  pageSize = 20,
  isLoading = false,
  onPageChange,
  filterLabel,
}: ApplicationTableProps) {
  const navigate = useNavigate();
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const start = page * pageSize + 1;
  const end = Math.min((page + 1) * pageSize, total);

  const handleView = (id: number) => {
    navigate(`/applications/${id}`);
  };

  return (
    <div className="flex flex-col gap-3">
      {/* Table header info */}
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>
          {isLoading
            ? 'Loading…'
            : total === 0
              ? 'No applications found'
              : `Showing ${start}–${end} of ${total}${filterLabel ? ` • ${filterLabel}` : ''}`}
        </span>
        <span>
          Page {page + 1} / {totalPages}
        </span>
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-xl border border-gray-200">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50 text-xs font-semibold uppercase tracking-wide text-gray-500">
              <tr>
                <th className="px-4 py-3 text-left">ID</th>
                <th className="px-4 py-3 text-left">Submitted</th>
                <th className="px-4 py-3 text-right">Risk Score</th>
                <th className="px-4 py-3 text-left">AI Decision</th>
                <th className="px-4 py-3 text-left">Override</th>
                <th className="px-4 py-3 text-center">Actions</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-gray-100 bg-white">
              {/* Loading skeleton */}
              {isLoading && (
                <>
                  <SkeletonRow />
                  <SkeletonRow />
                  <SkeletonRow />
                  <SkeletonRow />
                  <SkeletonRow />
                </>
              )}

              {/* Empty state */}
              {!isLoading && applications.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-16 text-center">
                    <div className="flex flex-col items-center gap-2 text-gray-400">
                      <Inbox size={32} />
                      <p className="text-sm font-medium">No applications found</p>
                      <p className="text-xs">Applications you submit will appear here.</p>
                    </div>
                  </td>
                </tr>
              )}

              {/* Data rows */}
              {!isLoading &&
                applications.map((app) => {
                  const effectiveDecision: DecisionType = app.officer_override ?? app.decision;
                  return (
                    <tr
                      key={app.id}
                      onClick={() => handleView(app.id)}
                      className="cursor-pointer transition-colors hover:bg-gray-50"
                    >
                      {/* ID */}
                      <td className="px-4 py-3 font-mono text-xs text-gray-500">
                        #{app.id}
                      </td>

                      {/* Date */}
                      <td className="px-4 py-3 text-gray-600">
                        {format(parseISO(app.scored_at), 'dd MMM yyyy')}
                        <span className="ml-1 text-xs text-gray-400">
                          {format(parseISO(app.scored_at), 'HH:mm')}
                        </span>
                      </td>

                      {/* Risk score */}
                      <td className="px-4 py-3 text-right">
                        <span
                          className={`font-bold tabular-nums ${
                            app.probability < 0.35
                              ? 'text-success-600'
                              : app.probability < 0.65
                                ? 'text-warning-600'
                                : 'text-danger-600'
                          }`}
                        >
                          {(app.probability * 100).toFixed(1)}%
                        </span>
                      </td>

                      {/* AI Decision */}
                      <td className="px-4 py-3">
                        <Badge decision={app.decision} size="sm" />
                      </td>

                      {/* Override */}
                      <td className="px-4 py-3">
                        {app.officer_override ? (
                          <Badge decision={app.officer_override} size="sm" />
                        ) : (
                          <span className="text-xs text-gray-300">—</span>
                        )}
                      </td>

                      {/* Actions */}
                      <td
                        className="px-4 py-3 text-center"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Button
                          variant="ghost"
                          size="sm"
                          leftIcon={<Eye size={13} />}
                          onClick={() => handleView(app.id)}
                        >
                          View
                        </Button>
                      </td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <Button
          variant="secondary"
          size="sm"
          leftIcon={<ChevronLeft size={14} />}
          disabled={page === 0 || isLoading}
          onClick={() => onPageChange(page - 1)}
        >
          Previous
        </Button>

        {/* Page dots */}
        <div className="flex items-center gap-1">
          {Array.from({ length: Math.min(totalPages, 7) }).map((_, i) => {
            const pageIdx =
              totalPages <= 7
                ? i
                : page < 4
                  ? i
                  : page > totalPages - 5
                    ? totalPages - 7 + i
                    : page - 3 + i;
            return (
              <button
                key={pageIdx}
                onClick={() => onPageChange(pageIdx)}
                className={`h-7 w-7 rounded-md text-xs font-medium transition-colors ${
                  pageIdx === page
                    ? 'bg-primary-600 text-white'
                    : 'text-gray-500 hover:bg-gray-100'
                }`}
              >
                {pageIdx + 1}
              </button>
            );
          })}
        </div>

        <Button
          variant="secondary"
          size="sm"
          rightIcon={<ChevronRight size={14} />}
          disabled={page >= totalPages - 1 || isLoading}
          onClick={() => onPageChange(page + 1)}
        >
          Next
        </Button>
      </div>
    </div>
  );
}
