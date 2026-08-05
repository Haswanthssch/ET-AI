"use client";

import Link from "next/link";
import { ALL_THEMES } from "@/lib/theme";

export default function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-slate-950">
      <div className="grid-bg absolute inset-0 opacity-40" />
      <div className="absolute -top-40 left-1/2 h-96 w-[40rem] -translate-x-1/2 rounded-full bg-rose-900/20 blur-3xl" />

      <div className="relative mx-auto max-w-6xl px-6 py-16">
        {/* Nav */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-slate-700 to-slate-900 text-lg font-black text-white ring-1 ring-slate-700">
              E
            </div>
            <div>
              <p className="text-lg font-bold text-white">ETAI</p>
              <p className="text-[10px] uppercase tracking-widest text-slate-500">
                EPC Intelligence Platform
              </p>
            </div>
          </div>
          <Link
            href="/login"
            className="rounded-xl bg-white px-5 py-2 text-sm font-semibold text-slate-900 transition hover:bg-slate-200"
          >
            Sign in
          </Link>
        </div>

        {/* Hero */}
        <div className="mt-24 max-w-3xl">
          <span className="inline-flex items-center rounded-full border border-slate-700 bg-slate-900/60 px-3 py-1 text-xs font-medium text-slate-300">
            Industrial AI · Hyperscale Data Centre EPC
          </span>
          <h1 className="mt-6 text-4xl font-black leading-tight text-white sm:text-6xl">
            A living intelligence layer for
            <span className="bg-gradient-to-r from-rose-400 via-amber-300 to-teal-300 bg-clip-text text-transparent">
              {" "}
              data centre delivery
            </span>
          </h1>
          <p className="mt-6 max-w-2xl text-lg text-slate-400">
            ETAI unifies specifications, submittals, schedules, procurement, RFIs
            and commissioning logs — turning reactive coordination into proactive,
            cited decision support powered by five specialised AI agents.
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            <Link
              href="/login"
              className="rounded-xl bg-gradient-to-r from-rose-600 to-amber-500 px-6 py-3 text-sm font-semibold text-white shadow-lg transition hover:opacity-90"
            >
              Launch platform →
            </Link>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="rounded-xl border border-slate-700 px-6 py-3 text-sm font-semibold text-slate-200 transition hover:border-slate-500"
            >
              API docs
            </a>
          </div>
        </div>

        {/* Role cards */}
        <div className="mt-24">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
            Role-based dashboards
          </p>
          <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {ALL_THEMES.map((t) => (
              <Link
                key={t.key}
                href="/login"
                className={`group relative overflow-hidden rounded-2xl border ${t.accentBorder} bg-slate-900/50 p-5 transition hover:-translate-y-1`}
              >
                <div
                  className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-r ${t.gradient}`}
                />
                <svg
                  viewBox="0 0 24 24"
                  className={`h-8 w-8 ${t.accentText}`}
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.6"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d={t.icon} />
                </svg>
                <h3 className="mt-4 text-base font-semibold text-white">
                  {t.name}
                </h3>
                <p className="mt-1 text-sm text-slate-400">{t.tagline}</p>
              </Link>
            ))}
          </div>
        </div>

        <footer className="mt-24 border-t border-slate-800/60 pt-6 text-xs text-slate-600">
          ETAI · Prepared by A. Nikhitha &amp; Ch. Haswanth Sai Sarath
        </footer>
      </div>
    </div>
  );
}
