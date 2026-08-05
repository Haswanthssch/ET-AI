"use client";

import { useState } from "react";
import { DashboardShell } from "@/components/DashboardShell";
import { Card } from "@/components/ui";
import { THEMES } from "@/lib/theme";
import { runCommissioning, CommissioningResult } from "@/lib/api";

const TIERS = ["I", "II", "III", "IV"];

const SAMPLE_LOG = `Generator load bank test: 2250kVA, transfer time 8.5s, voltage tolerance 3.2%, runtime 24h.
UPS test: runtime 45 min, output THD 3.8%, input 480V.
Cooling: supply temp 22.5C, humidity 45%RH, PUE 1.28.
Grounding resistance: 0.8 ohm.
Site availability measured: 99.985%. Concurrent maintenance verified. Fault tolerance verified.`;

export default function QaQcPage() {
  const [tier, setTier] = useState("III");
  const [log, setLog] = useState(SAMPLE_LOG);
  const [result, setResult] = useState<CommissioningResult | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  async function run() {
    setRunning(true);
    setResult(null);
    setError("");
    try {
      const res = await runCommissioning(log, tier);
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Commissioning check failed");
    } finally {
      setRunning(false);
    }
  }

  return (
    <DashboardShell theme={THEMES.qa_qc}>
      {error && (
        <div className="mb-6 rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
          {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Input */}
        <Card title="Commissioning Test Log" subtitle="Tier I–IV validator">
          <div className="space-y-3">
            <div>
              <label className="mb-2 block text-xs font-medium text-slate-400">
                Target Tier
              </label>
              <div className="flex gap-2">
                {TIERS.map((t) => (
                  <button
                    key={t}
                    onClick={() => setTier(t)}
                    className={`flex-1 rounded-xl border px-3 py-2 text-sm font-semibold transition ${
                      tier === t
                        ? "border-teal-500/50 bg-teal-500/10 text-teal-300"
                        : "border-slate-700 text-slate-400 hover:border-slate-500"
                    }`}
                  >
                    Tier {t}
                  </button>
                ))}
              </div>
            </div>
            <textarea
              value={log}
              onChange={(e) => setLog(e.target.value)}
              rows={10}
              className="w-full resize-none rounded-xl border border-slate-700 bg-slate-900/60 px-4 py-2.5 font-mono text-xs text-white outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-500/40"
            />
            <button
              onClick={run}
              disabled={running}
              className="w-full rounded-xl bg-gradient-to-r from-teal-600 to-teal-400 px-4 py-2.5 text-sm font-semibold text-slate-900 transition hover:opacity-90 disabled:opacity-50"
            >
              {running ? "Validating…" : "Validate & generate certificate"}
            </button>
          </div>
        </Card>

        {/* Result */}
        <Card title="Validation Result" subtitle="Uptime Institute Tier thresholds">
          {!result ? (
            <p className="text-sm text-slate-500">
              Run validation to verify metrics and auto-generate a Tier certificate.
            </p>
          ) : (
            <div className="space-y-4">
              <div
                className={`flex items-center justify-between rounded-xl p-4 ${
                  result.overall_pass
                    ? "bg-teal-500/10"
                    : "bg-rose-500/10"
                }`}
              >
                <div>
                  <p className="text-xs uppercase tracking-wider text-slate-400">
                    Tier {result.target_tier}
                  </p>
                  <p
                    className={`text-2xl font-bold ${
                      result.overall_pass ? "text-teal-300" : "text-rose-300"
                    }`}
                  >
                    {result.certificate.status}
                  </p>
                </div>
                <div className="text-right text-xs text-slate-400">
                  <p>{result.tier_analysis.passed_checks.length} passed</p>
                  <p>{result.tier_analysis.failed_checks.length} failed</p>
                  <p>{result.certificate.critical_failures} critical</p>
                </div>
              </div>

              <div>
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                  Checks
                </p>
                <div className="grid grid-cols-2 gap-2">
                  {result.tier_analysis.passed_checks.map((c) => (
                    <div
                      key={c.system}
                      className="flex items-center gap-2 rounded-lg bg-slate-900/60 px-3 py-2 text-xs"
                    >
                      <span className="text-teal-400">✓</span>
                      <span className="truncate text-slate-300">{c.system}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </Card>

        {/* Certificate */}
        {result && (
          <Card
            title="Tier Compliance Certificate"
            subtitle={`Issued ${result.certificate.issued_date}`}
            className="lg:col-span-2"
          >
            <pre className="max-h-96 overflow-auto whitespace-pre-wrap rounded-xl border border-slate-800 bg-slate-900/60 p-4 font-mono text-xs leading-relaxed text-slate-300">
              {result.certificate.certificate_text}
            </pre>
          </Card>
        )}
      </div>
    </DashboardShell>
  );
}
