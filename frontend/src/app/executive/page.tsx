"use client";

import { useEffect, useState } from "react";
import { DashboardShell } from "@/components/DashboardShell";
import { Card, StatTile, SeverityBadge, ProgressBar, Sparkline } from "@/components/ui";
import { THEMES } from "@/lib/theme";
import {
  getExecutiveSummary,
  predictRisk,
  ExecutiveSummary,
  RiskResult,
} from "@/lib/api";

export default function ExecutivePage() {
  const [data, setData] = useState<ExecutiveSummary | null>(null);
  const [risk, setRisk] = useState<RiskResult | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getExecutiveSummary()
      .then(setData)
      .catch((e) => setError(e.message));
    predictRisk("GEN-CAT-01")
      .then(setRisk)
      .catch(() => {});
  }, []);

  return (
    <DashboardShell theme={THEMES.executive}>
      {error && (
        <div className="mb-6 rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
          {error} — is the backend running on :8000?
        </div>
      )}

      {!data ? (
        <p className="text-slate-400">Loading program health…</p>
      ) : (
        <div className="space-y-6">
          <p className="text-sm text-slate-400">{data.project}</p>

          {/* KPI row */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatTile
              label="Schedule Health"
              value={data.kpis.schedule_health_pct}
              unit="%"
              accent="text-rose-400"
            />
            <StatTile
              label="Projected Slip"
              value={data.kpis.project_slip_days}
              unit="days"
              accent="text-amber-400"
              hint="Driven by GEN-CAT-01"
            />
            <StatTile
              label="Critical NCRs"
              value={data.kpis.critical_ncrs}
              accent="text-rose-400"
            />
            <StatTile
              label="Commissioning"
              value={data.kpis.commissioning_progress_pct}
              unit="%"
              accent="text-teal-300"
            />
          </div>

          <div className="grid gap-6 lg:grid-cols-3">
            {/* Live alerts */}
            <Card
              title="Live Risk Alerts"
              subtitle="Self-healing agents · real-time"
              className="lg:col-span-2"
            >
              <div className="space-y-3">
                {data.alerts.map((a, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-3 rounded-xl border border-slate-800 bg-slate-900/40 p-4"
                  >
                    <div className="mt-0.5">
                      <SeverityBadge severity={a.severity} />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="font-semibold text-slate-100">{a.title}</p>
                        {a.equipment_tag && (
                          <span className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-[11px] text-slate-300">
                            {a.equipment_tag}
                          </span>
                        )}
                      </div>
                      <p className="mt-1 text-sm text-slate-400">{a.detail}</p>
                      <p className="mt-1 text-xs text-slate-500">
                        Source: {a.source}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* SLA + trend */}
            <div className="space-y-6">
              <Card title="Risk Health Trend" subtitle="Last 7 periods">
                <Sparkline data={data.risk_trend} stroke="#e11d48" />
                <div className="mt-2 flex items-center justify-between text-xs text-slate-400">
                  <span>Trend</span>
                  <span className="font-semibold text-rose-400">
                    {data.risk_trend[data.risk_trend.length - 1]}%
                  </span>
                </div>
              </Card>
              <Card title="RFI SLA">
                <div className="flex items-end justify-between">
                  <div>
                    <p className="text-3xl font-bold text-rose-400">
                      {data.sla.rfi_response_hours_avg}h
                    </p>
                    <p className="text-xs text-slate-400">
                      avg response · target {data.sla.rfi_sla_hours}h
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-teal-300">
                      {data.sla.on_time_pct}%
                    </p>
                    <p className="text-xs text-slate-400">on time</p>
                  </div>
                </div>
              </Card>
            </div>
          </div>

          {/* Phase progress + CPM cascade */}
          <div className="grid gap-6 lg:grid-cols-2">
            <Card title="Phase Progress">
              <div className="space-y-4">
                {data.phase_progress.map((p) => (
                  <div key={p.phase}>
                    <div className="mb-1 flex items-center justify-between text-sm">
                      <span className="text-slate-300">{p.phase}</span>
                      <span className="text-slate-400">{p.pct}%</span>
                    </div>
                    <ProgressBar
                      value={p.pct}
                      colorClass="bg-gradient-to-r from-rose-500 to-amber-400"
                    />
                  </div>
                ))}
              </div>
            </Card>

            <Card
              title="Critical Path Cascade"
              subtitle="GEN-CAT-01 delay impact (Risk Engine)"
            >
              {risk ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-3">
                    <div className="rounded-xl bg-slate-900/60 p-3 text-center">
                      <p className="text-2xl font-bold text-rose-400">
                        {risk.cpm_cascade.project_slip_days}
                      </p>
                      <p className="text-[11px] text-slate-400">slip days</p>
                    </div>
                    <div className="rounded-xl bg-slate-900/60 p-3 text-center">
                      <p className="text-2xl font-bold text-amber-400">
                        {risk.cpm_cascade.critical_path_impacted_tasks}
                      </p>
                      <p className="text-[11px] text-slate-400">tasks hit</p>
                    </div>
                    <div className="rounded-xl bg-slate-900/60 p-3 text-center">
                      <p className="text-2xl font-bold text-rose-300">
                        {Math.round(risk.delay_probability * 100)}%
                      </p>
                      <p className="text-[11px] text-slate-400">delay prob</p>
                    </div>
                  </div>
                  <div>
                    <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                      Top mitigation
                    </p>
                    <p className="rounded-xl border border-slate-800 bg-slate-900/40 p-3 text-sm text-slate-300">
                      {risk.mitigations[0]}
                    </p>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-slate-500">Computing cascade…</p>
              )}
            </Card>
          </div>
        </div>
      )}
    </DashboardShell>
  );
}
