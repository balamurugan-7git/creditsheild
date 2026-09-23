// ============================================================
// CrediShield AI – Risk Result Card
// Displays AI prediction: probability gauge, decision badge,
// SHAP factor explanations, and officer override info
// ============================================================

import React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
} from 'recharts';
import { format, parseISO } from 'date-fns';
import {
  TrendingUp,
  TrendingDown,
  AlertCircle,
  CheckCircle2,
  XCircle,
  ShieldAlert,
  Clock,
  Cpu,
} from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import Badge, { decisionLabel } from '@/components/ui/Badge';
import type { Application, ShapFactor } from '@/types';

// ---- Helpers ---- //
function getRiskColor(probability: number): {
  text: string;
  bg: string;
  ring: string;
  gauge: string;
} {
  if (probability < 0.35) {
    return { text: 'text-success-600', bg: 'bg-success-50', ring: 'ring-success-200', gauge: '#16a34a' };
  } else if (probability < 0.65) {
    return { text: 'text-warning-600', bg: 'bg-warning-50', ring: 'ring-yellow-200', gauge: '#eab308' };
  }
  return { text: 'text-danger-600', bg: 'bg-danger-50', ring: 'ring-danger-200', gauge: '#dc2626' };
}

// ---- Gauge Chart ---- //
interface GaugeChartProps {
  probability: number;
}

function GaugeChart({ probability }: GaugeChartProps) {
  const pct = Math.round(probability * 100);
  const { gauge } = getRiskColor(probability);

  // Build a half-donut: filled arc + unfilled arc
  const data = [
    { value: pct },
    { value: 100 - pct },
  ];

  return (
    <div className="relative flex flex-col items-center">
      <ResponsiveContainer width={180} height={100}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="100%"
            startAngle={180}
            endAngle={0}
            innerRadius={60}
            outerRadius={80}
            dataKey="value"
            strokeWidth={0}
          >
            <Cell fill={gauge} />
            <Cell fill="#e5e7eb" />
          </Pie>
        </PieChart>
      </ResponsiveContainer>
      {/* Centered percentage label */}
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1 text-center">
        <span className={`text-3xl font-bold ${getRiskColor(probability).text}`}>
          {pct}%
        </span>
        <p className="text-xs text-gray-400 mt-0.5">Default Risk</p>
      </div>
    </div>
  );
}

// ---- SHAP Factor Row ---- //
interface ShapRowProps {
  factor: ShapFactor;
}

function ShapRow({ factor }: ShapRowProps) {
  const increases = factor.direction === 'increases_risk';
  return (
    <li className="flex items-start gap-2.5 py-2">
      <span
        className={`mt-0.5 flex-shrink-0 rounded-full p-1 ${
          increases ? 'bg-danger-100 text-danger-600' : 'bg-success-100 text-success-600'
        }`}
      >
        {increases ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
      </span>
      <span className="text-sm text-gray-700">
        <span className="font-medium">{factor.display_name}</span>{' '}
        <span className={increases ? 'text-danger-600 font-medium' : 'text-success-600 font-medium'}>
          {increases ? 'increases' : 'decreases'}
        </span>{' '}
        your risk
        <span className="ml-2 text-xs text-gray-400">
          ({increases ? '+' : ''}{factor.shap_value.toFixed(3)})
        </span>
      </span>
    </li>
  );
}

// ---- Main Component ---- //
interface RiskResultCardProps {
  application: Application;
  /** Animate entrance */
  animate?: boolean;
}

export default function RiskResultCard({ application, animate = true }: RiskResultCardProps) {
  const {
    probability,
    decision,
    model_version,
    scored_at,
    shap_top_factors,
    officer_override,
    override_reason,
    override_at,
  } = application;

  const colors = getRiskColor(probability);
  const effectiveDecision = officer_override ?? decision;

  const DecisionIcon =
    effectiveDecision === 'approved'
      ? CheckCircle2
      : effectiveDecision === 'rejected'
        ? XCircle
        : AlertCircle;

  return (
    <div className={animate ? 'animate-slide-up' : ''}>
      {/* Override Banner */}
      {officer_override && (
        <div className="mb-3 flex items-center gap-2 rounded-lg border border-yellow-300 bg-yellow-50 px-4 py-3">
          <ShieldAlert size={16} className="flex-shrink-0 text-yellow-600" />
          <p className="text-sm text-yellow-800">
            <span className="font-semibold">Officer Override Applied: </span>
            Decision changed to{' '}
            <span className="font-bold">{decisionLabel(officer_override)}</span>
            {override_reason && ` — "${override_reason}"`}
            {override_at && (
              <span className="text-yellow-600 ml-1">
                on {format(parseISO(override_at), 'dd MMM yyyy HH:mm')}
              </span>
            )}
          </p>
        </div>
      )}

      <Card>
        <CardHeader separator>
          <CardTitle>AI Risk Assessment</CardTitle>
          <Badge decision={effectiveDecision} size="md" />
        </CardHeader>

        <CardContent>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {/* Left: Gauge + decision summary */}
            <div className="flex flex-col items-center gap-4">
              <GaugeChart probability={probability} />

              {/* Decision summary box */}
              <div
                className={`w-full rounded-lg ${colors.bg} ring-1 ${colors.ring} px-4 py-3 flex items-center gap-3`}
              >
                <DecisionIcon size={20} className={colors.text} />
                <div>
                  <p className="text-xs text-gray-500">Final Decision</p>
                  <p className={`text-base font-bold ${colors.text}`}>
                    {decisionLabel(effectiveDecision)}
                  </p>
                </div>
              </div>

              {/* Meta info */}
              <div className="w-full space-y-1.5 text-xs text-gray-400">
                <div className="flex items-center gap-1.5">
                  <Cpu size={11} />
                  <span>Model: {model_version}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Clock size={11} />
                  <span>Scored: {format(parseISO(scored_at), 'dd MMM yyyy HH:mm:ss')}</span>
                </div>
              </div>
            </div>

            {/* Right: SHAP explanations */}
            <div>
              <h4 className="mb-2 text-sm font-semibold text-gray-700">
                Key Factors Influencing This Decision
              </h4>
              {shap_top_factors.length === 0 ? (
                <p className="text-sm text-gray-400">No factor explanation available.</p>
              ) : (
                <ul className="divide-y divide-gray-100">
                  {shap_top_factors.map((factor) => (
                    <ShapRow key={factor.feature} factor={factor} />
                  ))}
                </ul>
              )}

              {/* Risk legend */}
              <div className="mt-4 rounded-lg bg-gray-50 px-3 py-2 text-xs text-gray-500">
                <p className="font-medium text-gray-600 mb-1">Risk Scale</p>
                <div className="flex items-center gap-3">
                  <span className="flex items-center gap-1">
                    <span className="h-2 w-2 rounded-full bg-success-500 inline-block" />
                    Low (&lt;35%)
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="h-2 w-2 rounded-full bg-warning-400 inline-block" />
                    Medium (35–65%)
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="h-2 w-2 rounded-full bg-danger-500 inline-block" />
                    High (&gt;65%)
                  </span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
