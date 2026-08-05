"use client";

import { useRef, useState } from "react";
import { DashboardShell } from "@/components/DashboardShell";
import { Card, SeverityBadge } from "@/components/ui";
import { THEMES } from "@/lib/theme";
import { rfiCopilot, visionParse, RfiResult, VisionResult } from "@/lib/api";

interface ChatMsg {
  role: "user" | "assistant";
  content: string;
  citations?: string[];
}

const SUGGESTIONS = [
  "How was the MEP coordination conflict in IT Hall A resolved?",
  "What is the TIA-942 cable tray separation requirement?",
  "Show critical priority RFIs on electrical grounding",
  "How was the seismic bracing non-compliance resolved?",
];

export default function EngineerPage() {
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const [vision, setVision] = useState<VisionResult | null>(null);
  const [parsing, setParsing] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  async function ask(q: string) {
    if (!q.trim() || loading) return;
    const userMsg: ChatMsg = { role: "user", content: q };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const res: RfiResult = await rfiCopilot(q);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: res.answer, citations: res.citations },
      ]);
    } catch (e) {
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content:
            e instanceof Error
              ? `${e.message} — is the backend running?`
              : "Request failed.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setParsing(true);
    setVision(null);
    try {
      const res = await visionParse(file);
      setVision(res);
    } catch {
      /* ignore */
    } finally {
      setParsing(false);
    }
  }

  return (
    <DashboardShell theme={THEMES.engineer}>
      <div className="grid gap-6 lg:grid-cols-3">
        {/* RFI Copilot */}
        <div className="lg:col-span-2">
          <Card
            title="RFI Copilot"
            subtitle="Cited RAG answers · at least one source guaranteed"
            className="flex h-[560px] flex-col"
          >
            <div className="flex-1 space-y-4 overflow-y-auto pr-1">
              {messages.length === 0 && (
                <div className="space-y-3">
                  <p className="text-sm text-slate-400">
                    Ask about specifications, RFIs, or contractual queries. Every
                    answer carries inline citations.
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {SUGGESTIONS.map((s) => (
                      <button
                        key={s}
                        onClick={() => ask(s)}
                        className="rounded-lg border border-orange-500/30 bg-orange-500/5 px-3 py-1.5 text-left text-xs text-orange-200 transition hover:bg-orange-500/10"
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((m, i) => (
                <div
                  key={i}
                  className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${
                      m.role === "user"
                        ? "bg-orange-500/20 text-orange-50"
                        : "border border-slate-800 bg-slate-900/60 text-slate-200"
                    }`}
                  >
                    <p className="whitespace-pre-wrap leading-relaxed">{m.content}</p>
                    {m.citations && m.citations.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {m.citations.map((c) => (
                          <span
                            key={c}
                            className="rounded bg-orange-500/10 px-2 py-0.5 font-mono text-[11px] text-orange-300"
                          >
                            {c}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="flex justify-start">
                  <div className="rounded-2xl border border-slate-800 bg-slate-900/60 px-4 py-3 text-sm text-slate-400">
                    <span className="animate-pulseglow">Retrieving & reasoning…</span>
                  </div>
                </div>
              )}
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                ask(input);
              }}
              className="mt-4 flex gap-2"
            >
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask the RFI copilot…"
                className="flex-1 rounded-xl border border-slate-700 bg-slate-900/60 px-4 py-2.5 text-sm text-white outline-none focus:border-orange-500 focus:ring-2 focus:ring-orange-500/40"
              />
              <button
                type="submit"
                disabled={loading}
                className="rounded-xl bg-gradient-to-r from-orange-600 to-orange-400 px-5 py-2.5 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-50"
              >
                Send
              </button>
            </form>
          </Card>
        </div>

        {/* Vision parser */}
        <Card title="Vision Parser" subtitle="P&ID / drawing deviation analysis">
          <input
            ref={fileRef}
            type="file"
            onChange={onFile}
            className="hidden"
            accept="image/*,.pdf"
          />
          <button
            onClick={() => fileRef.current?.click()}
            className="mb-4 w-full rounded-xl border-2 border-dashed border-orange-500/40 bg-orange-500/5 px-4 py-6 text-sm text-orange-200 transition hover:bg-orange-500/10"
          >
            {parsing ? "Parsing drawing…" : "Upload drawing to analyse"}
          </button>

          {vision && (
            <div className="space-y-4 text-sm">
              <div className="rounded-xl bg-slate-900/60 p-3">
                <p className="font-semibold text-slate-100">{vision.system_type}</p>
                <p className="text-xs text-slate-400">
                  {vision.drawing_metadata.number} · Rev{" "}
                  {vision.drawing_metadata.revision} · {vision.drawing_metadata.scale}
                </p>
                <p className="mt-1 text-xs text-slate-500">
                  Confidence {Math.round(vision.confidence * 100)}%
                </p>
              </div>

              <div>
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                  Deviations ({vision.deviation_analysis.total_deviations})
                </p>
                <div className="space-y-2">
                  {vision.deviation_analysis.deviations.map((d, i) => (
                    <div
                      key={i}
                      className="rounded-xl border border-slate-800 bg-slate-900/40 p-3"
                    >
                      <div className="mb-1 flex items-center justify-between">
                        <SeverityBadge severity={d.severity} />
                        <span className="font-mono text-[11px] text-orange-300">
                          {d.spec_ref}
                        </span>
                      </div>
                      <p className="text-slate-300">{d.issue}</p>
                      <p className="mt-1 text-xs text-slate-500">{d.location}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </Card>
      </div>
    </DashboardShell>
  );
}
