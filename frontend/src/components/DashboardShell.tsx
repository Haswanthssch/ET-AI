"use client";

import { useEffect, useState, ReactNode } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { clearSession, getRole, getUsername, isAuthenticated } from "@/lib/auth";
import { ALL_THEMES, RoleTheme } from "@/lib/theme";

export function DashboardShell({
  theme,
  children,
}: {
  theme: RoleTheme;
  children: ReactNode;
}) {
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [username, setUsername] = useState<string>("");

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    setUsername(getUsername() || "");
    setReady(true);
  }, [router]);

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950">
        <div className="animate-pulseglow text-slate-400">Loading…</div>
      </div>
    );
  }

  const currentRole = getRole();

  function logout() {
    clearSession();
    router.replace("/login");
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 z-20 flex w-64 flex-col border-r border-slate-800/60 bg-slate-900/50 backdrop-blur">
        <Link href="/" className="flex items-center gap-2 px-6 py-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-slate-700 to-slate-900 text-sm font-black text-white ring-1 ring-slate-700">
            E
          </div>
          <div>
            <p className="text-sm font-bold leading-none">ETAI</p>
            <p className="mt-0.5 text-[10px] uppercase tracking-widest text-slate-500">
              EPC Intelligence
            </p>
          </div>
        </Link>

        <nav className="mt-2 flex-1 space-y-1 px-3">
          {ALL_THEMES.map((t) => {
            const active = t.key === theme.key;
            return (
              <Link
                key={t.key}
                href={t.path}
                className={`group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition ${
                  active
                    ? `${t.accentBg} ${t.accentText} ${t.glow} font-semibold`
                    : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
                }`}
              >
                <svg
                  viewBox="0 0 24 24"
                  className="h-5 w-5 shrink-0"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d={t.icon} />
                </svg>
                <span className="truncate">{t.name}</span>
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-slate-800/60 p-4">
          <div className="mb-3 rounded-xl bg-slate-800/40 px-3 py-2">
            <p className="truncate text-xs font-medium text-slate-200">{username}</p>
            <p className="mt-0.5 text-[10px] uppercase tracking-wider text-slate-500">
              {currentRole}
            </p>
          </div>
          <button
            onClick={logout}
            className="w-full rounded-xl border border-slate-700 px-3 py-2 text-xs font-medium text-slate-300 transition hover:border-slate-500 hover:text-white"
          >
            Sign out
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="pl-64">
        {/* Themed hero bar */}
        <header
          className={`relative overflow-hidden border-b border-slate-800/60 bg-gradient-to-r ${theme.gradient}`}
        >
          <div className="grid-bg absolute inset-0 opacity-40" />
          <div className="relative px-8 py-8">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/60">
              {theme.tagline}
            </p>
            <h1 className="mt-1 text-2xl font-bold text-white sm:text-3xl">
              {theme.name}
            </h1>
          </div>
        </header>

        <main className="px-8 py-8">{children}</main>
      </div>
    </div>
  );
}
