"use client";

import { useEffect, useState } from "react";
import { DashboardShell } from "@/components/DashboardShell";
import { Card, StatTile, SeverityBadge } from "@/components/ui";
import { THEMES } from "@/lib/theme";
import {
  getSupplyChain,
  checkCompliance,
  SupplyChainResult,
  ComplianceResult,
} from "@/lib/api";

const statusColor: Record<string, string> = {
  "Customs Hold": "text-rose-300 bg-rose-500/10",
  "In Transit": "text-amber-300 bg-amber-500/10",
  Manufacturing: "text-sky-300 bg-sky-500/10",
  Delivered: "text-teal-300 bg-teal-500/10",
};

export default function ProcurementPage() {
  const [sc, setSc] = useState<SupplyChainResult | null>(null);
  const [error, setError] = useState("");

  // Compliance checker
  const [submittal, setSubmittal] = useState(
    "Caterpillar 2500kVA generator submittal — voltage tolerance ±8%, IP54 enclosure, seismic anchorage to IBC 2021 Zone 4.",
  );
  const [tag, setTag] = useState("GEN-CAT-01");
  const [compliance, setCompliance] = useState<ComplianceResult | null>(null);
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    getSupplyChain()
      .then(setSc)
      .catch((e) => setError(e.message));
  }, []);

  async function runCheck() {
    setChecking(true);
    setCompliance(null);
    try {
      const res = await checkCompliance(submittal, tag);
      setCompliance(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Compliance check failed");
    } finally {
      setChecking(false);
    }
  }

  return (
    <DashboardShell theme={THEMES.procurement}>
      {error && (
        <div className="mb-6 rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
          {error}
        </div>
      )}

      <div className="space-y-6">
        {/* Supply KPIs */}
        {sc && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatTile label="Tracked Items" value={sc.summary.total_items} accent="text-amber-400" />
            <StatTile label="At Risk" value={sc.summary.at_risk} accent="text-rose-400" />
            <StatTile
              label="On Critical Path"
              value={sc.summary.on_critical_path}
              accent="text-amber-300"
            />
            <StatTile
              label="Customs Holds"
              value={sc.summary.customs_holds}
              accent="text-rose-400"
            />
          </div>
        )}

        {/* Supply chain table */}
        <Card title="Supply Chain Visibility" subtitle="Critical equipment tracking">
          {!sc ? (
            <p className="text-sm text-slate-500">Loading supply chain…</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-800 text-left text-xs uppercase tracking-wider text-slate-500">
                    <th className="pb-3 pr-4">Tag</th>
                    <th className="pb-3 pr-4">Equipment</th>
                    <th className="pb-3 pr-4">Vendor</th>
                    <th className="pb-3 pr-4">Status</th>
                    <th className="pb-3 pr-4">Delay</th>
                    <th className="pb-3 pr-4">ETA</th>
                    <th className="pb-3">Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {sc.items.map((it) => (
                    <tr
                      key={it.tag}
                      className="border-b border-slate-800/50 last:border-0"
                    >
                      <td className="py-3 pr-4">
                        <span className="font-mono text-xs text-amber-300">
                          {it.tag}
                        </span>
                        {it.critical_path && (
                          <span className="ml-2 rounded bg-rose-500/10 px-1.5 py-0.5 text-[10px] font-semibold text-rose-300">
                            CP
                          </span>
                        )}
                      </td>
                      <td className="py-3 pr-4 text-slate-300">{it.description}</td>
                      <td className="py-3 pr-4 text-slate-400">{it.vendor}</td>
                      <td className="py-3 pr-4">
                        <span
                          className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                            statusColor[it.status] || "text-slate-300 bg-slate-500/10"
                          }`}
                        >
                          {it.status}
                        </span>
                      </td>
                      <td className="py-3 pr-4 text-slate-300">
                        {it.delay_days > 0 ? (
                          <span className="text-rose-300">+{it.delay_days}d</span>
                        ) : (
                          <span className="text-teal-300">on time</span>
                        )}
                      </td>
                      <td className="py-3 pr-4 text-slate-400">{it.eta}</td>
                      <td className="py-3">
                        <SeverityBadge severity={it.risk} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        {/* Compliance checker */}
        <div className="grid gap-6 lg:grid-cols-2">
          <Card title="Spec Compliance Checker" subtitle="Compliance Agent · RAG + critic">
            <div className="space-y-3">
              <input
                value={tag}
                onChange={(e) => setTag(e.target.value)}
                placeholder="Equipment tag"
                className="w-full rounded-xl border border-slate-700 bg-slate-900/60 px-4 py-2.5 text-sm text-white outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/50"
              />
              <textarea
                value={submittal}
                onChange={(e) => setSubmittal(e.target.value)}
                rows={5}
                placeholder="Paste vendor submittal text…"
                className="w-full resize-none rounded-xl border border-slate-700 bg-slate-900/60 px-4 py-2.5 text-sm text-white outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/50"
              />
              <button
                onClick={runCheck}
                disabled={checking}
                className="w-full rounded-xl bg-gradient-to-r from-amber-600 to-amber-400 px-4 py-2.5 text-sm font-semibold text-slate-900 transition hover:opacity-90 disabled:opacity-50"
              >
                {checking ? "Analysing…" : "Run compliance check"}
              </button>
            </div>
          </Card>

          <Card title="Findings" subtitle="Severity-ranked non-conformances">
            {!compliance ? (
              <p className="text-sm text-slate-500">
                Run a check to see findings with exact spec references.
              </p>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <span
                    className={`rounded-lg px-3 py-1 text-sm font-bold ${
                      compliance.verdict.includes("NON")
                        ? "bg-rose-500/10 text-rose-300"
                        : "bg-teal-500/10 text-teal-300"
                    }`}
                  >
                    {compliance.verdict}
                  </span>
                  {compliance.self_healing_triggered && (
                    <span className="text-xs text-slate-500">
                      ✓ critic self-heal
                    </span>
                  )}
                </div>
                <p className="text-sm text-slate-400">{compliance.summary}</p>
                <div className="space-y-2">
                  {compliance.findings.map((f, i) => (
                    <div
                      key={i}
                      className="rounded-xl border border-slate-800 bg-slate-900/40 p-3"
                    >
                      <div className="mb-1 flex items-center justify-between">
                        <SeverityBadge severity={f.severity} />
                        <span className="font-mono text-[11px] text-amber-300">
                          {f.spec_ref}
                        </span>
                      </div>
                      <p className="text-sm text-slate-300">{f.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>
        </div>
      </div>
    </DashboardShell>
  );
}
