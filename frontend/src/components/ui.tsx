import { ReactNode } from "react";

export function Card({
  children,
  className = "",
  title,
  subtitle,
  action,
}: {
  children: ReactNode;
  className?: string;
  title?: string;
  subtitle?: string;
  action?: ReactNode;
}) {
  return (
    <div
      className={`glass rounded-2xl p-5 animate-fade-in ${className}`}
    >
      {(title || action) && (
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            {title && (
              <h3 className="text-sm font-semibold tracking-wide text-slate-100">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="mt-0.5 text-xs text-slate-400">{subtitle}</p>
            )}
          </div>
          {action}
        </div>
      )}
      {children}
    </div>
  );
}

export function StatTile({
  label,
  value,
  unit,
  hint,
  accent = "text-slate-100",
}: {
  label: string;
  value: string | number;
  unit?: string;
  hint?: string;
  accent?: string;
}) {
  return (
    <div className="glass rounded-2xl p-4 animate-fade-in">
      <p className="text-xs uppercase tracking-wider text-slate-400">{label}</p>
      <p className={`mt-2 text-3xl font-bold ${accent}`}>
        {value}
        {unit && <span className="ml-1 text-base font-medium text-slate-400">{unit}</span>}
      </p>
      {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
    </div>
  );
}

export function SeverityBadge({ severity }: { severity: string }) {
  const s = severity.toLowerCase();
  let cls = "text-slate-300 bg-slate-500/10 border-slate-500/30";
  if (s === "critical") cls = "text-rose-300 bg-rose-500/10 border-rose-500/40";
  else if (s === "high" || s === "major")
    cls = "text-amber-300 bg-amber-500/10 border-amber-500/40";
  else if (s === "medium")
    cls = "text-yellow-300 bg-yellow-500/10 border-yellow-500/40";
  else if (s === "low" || s === "info" || s === "minor")
    cls = "text-teal-300 bg-teal-500/10 border-teal-500/40";
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide ${cls}`}
    >
      {severity}
    </span>
  );
}

export function ProgressBar({
  value,
  colorClass = "bg-teal-400",
}: {
  value: number;
  colorClass?: string;
}) {
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-slate-700/50">
      <div
        className={`h-full rounded-full ${colorClass} transition-all duration-700`}
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  );
}

// Minimal dependency-free sparkline.
export function Sparkline({
  data,
  stroke = "#e11d48",
}: {
  data: number[];
  stroke?: string;
}) {
  if (!data.length) return null;
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const w = 240;
  const h = 60;
  const pts = data
    .map((d, i) => {
      const x = (i / (data.length - 1)) * w;
      const y = h - ((d - min) / range) * h;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="h-16 w-full" preserveAspectRatio="none">
      <polyline
        points={pts}
        fill="none"
        stroke={stroke}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
