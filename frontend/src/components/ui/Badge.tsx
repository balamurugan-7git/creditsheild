// ============================================================
// CrediShield AI – Badge Component
// For decision status labels and generic tags
// ============================================================

import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { CheckCircle, AlertTriangle, XCircle } from 'lucide-react';
import type { DecisionType } from '@/types';

// ---- Variant definitions ---- //
export type BadgeVariant =
  | 'approved'
  | 'manual_review'
  | 'rejected'
  | 'default'
  | 'primary'
  | 'info'
  | 'success'
  | 'warning'
  | 'danger';

const variantStyles: Record<BadgeVariant, string> = {
  approved:
    'bg-success-100 text-success-700 border-success-200',
  manual_review:
    'bg-warning-100 text-yellow-700 border-yellow-200',
  rejected:
    'bg-danger-100 text-danger-700 border-danger-200',
  default:
    'bg-gray-100 text-gray-700 border-gray-200',
  primary:
    'bg-primary-100 text-primary-700 border-primary-200',
  info:
    'bg-blue-100 text-blue-700 border-blue-200',
  success:
    'bg-success-100 text-success-700 border-success-200',
  warning:
    'bg-warning-100 text-yellow-700 border-yellow-200',
  danger:
    'bg-danger-100 text-danger-700 border-danger-200',
};

// ---- Decision icon map ---- //
const DecisionIcon: Record<DecisionType, React.FC<{ size?: number }>> = {
  approved:      ({ size = 12 }) => <CheckCircle size={size} />,
  manual_review: ({ size = 12 }) => <AlertTriangle size={size} />,
  rejected:      ({ size = 12 }) => <XCircle size={size} />,
};

/** Human-readable label for a decision type */
export function decisionLabel(decision: DecisionType): string {
  switch (decision) {
    case 'approved':      return 'Approved';
    case 'manual_review': return 'Manual Review';
    case 'rejected':      return 'Rejected';
  }
}

// ---- Props ---- //
export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** Use a DecisionType to auto-select variant + icon + label */
  decision?: DecisionType;
  /** Or supply a manual variant */
  variant?: BadgeVariant;
  size?: 'sm' | 'md';
  showIcon?: boolean;
}

// ---- Component ---- //
export default function Badge({
  decision,
  variant,
  size = 'md',
  showIcon = true,
  children,
  className,
  ...rest
}: BadgeProps) {
  // Resolve variant: decision prop takes precedence
  const resolvedVariant: BadgeVariant = decision ?? variant ?? 'default';

  // Resolve icon & label when decision is provided
  const Icon = decision ? DecisionIcon[decision] : null;
  const label = decision ? decisionLabel(decision) : children;

  return (
    <span
      className={twMerge(
        clsx(
          'inline-flex items-center gap-1 rounded-full border font-medium',
          size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs',
          variantStyles[resolvedVariant],
        ),
        className,
      )}
      {...rest}
    >
      {showIcon && Icon && <Icon size={11} />}
      {label}
    </span>
  );
}
