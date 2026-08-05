"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { login } from "@/lib/api";
import { roleToPath, saveSession } from "@/lib/auth";
import { THEMES } from "@/lib/theme";

const ROLE_LABELS: Record<string, string> = {
  executive: "Executive",
  procurement: "Procurement",
  engineer: "Engineer",
  qa_qc: "QA / QC",
  admin: "Admin",
};

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("admin@etai.com");
  const [password, setPassword] = useState("etai123");
  const [roles, setRoles] = useState<string[]>([]);
  const [selectedRole, setSelectedRole] = useState<string>("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const result = await login(username, password, selectedRole || undefined);
      if (result.ok) {
        const role = selectedRole || roles[0] || "executive";
        saveSession(result.token, role, username);
        router.push(roleToPath[role] || "/executive");
        return;
      }
      if (result.needsRole) {
        setRoles(result.roles);
        // Auto-select if only one role
        if (result.roles.length === 1) {
          const only = result.roles[0];
          const r2 = await login(username, password, only);
          if (r2.ok) {
            saveSession(r2.token, only, username);
            router.push(roleToPath[only] || "/executive");
            return;
          }
        }
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? `${err.message}. Is the backend running on :8000?`
          : "Login failed",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-slate-950 px-4">
      <div className="grid-bg absolute inset-0 opacity-40" />
      <div className="absolute -top-24 right-1/4 h-80 w-80 rounded-full bg-teal-900/20 blur-3xl" />
      <div className="absolute bottom-0 left-1/4 h-80 w-80 rounded-full bg-rose-900/20 blur-3xl" />

      <div className="relative w-full max-w-md">
        <Link href="/" className="mb-8 flex items-center justify-center gap-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-slate-700 to-slate-900 text-lg font-black text-white ring-1 ring-slate-700">
            E
          </div>
          <span className="text-xl font-bold text-white">ETAI</span>
        </Link>

        <div className="glass rounded-2xl p-8">
          <h1 className="text-xl font-bold text-white">Sign in</h1>
          <p className="mt-1 text-sm text-slate-400">
            Access your EPC intelligence dashboard.
          </p>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-400">
                Email
              </label>
              <input
                type="email"
                value={username}
                onChange={(e) => {
                  setUsername(e.target.value);
                  setRoles([]);
                  setSelectedRole("");
                }}
                className="w-full rounded-xl border border-slate-700 bg-slate-900/60 px-4 py-2.5 text-sm text-white outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-600"
                placeholder="you@etai.com"
                required
              />
            </div>

            <div>
              <label className="mb-1 block text-xs font-medium text-slate-400">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-xl border border-slate-700 bg-slate-900/60 px-4 py-2.5 text-sm text-white outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-600"
                placeholder="••••••••"
                required
              />
            </div>

            {roles.length > 1 && (
              <div>
                <label className="mb-2 block text-xs font-medium text-slate-400">
                  Choose a role to continue
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {roles.map((r) => {
                    const t = THEMES[r];
                    const active = selectedRole === r;
                    return (
                      <button
                        key={r}
                        type="button"
                        onClick={() => setSelectedRole(r)}
                        className={`rounded-xl border px-3 py-2 text-sm font-medium transition ${
                          active
                            ? t
                              ? `${t.accentBorder} ${t.accentBg} ${t.accentText}`
                              : "border-slate-400 bg-slate-700 text-white"
                            : "border-slate-700 text-slate-300 hover:border-slate-500"
                        }`}
                      >
                        {ROLE_LABELS[r] || r}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {error && (
              <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-2.5 text-sm text-rose-300">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading || (roles.length > 1 && !selectedRole)}
              className="w-full rounded-xl bg-gradient-to-r from-rose-600 to-amber-500 px-4 py-2.5 text-sm font-semibold text-white shadow-lg transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading
                ? "Signing in…"
                : roles.length > 1
                  ? "Continue"
                  : "Sign in"}
            </button>
          </form>

          <div className="mt-6 rounded-xl border border-slate-800 bg-slate-900/40 p-3 text-xs text-slate-400">
            <p className="font-semibold text-slate-300">Demo credentials</p>
            <p className="mt-1">
              <span className="text-slate-200">admin@etai.com</span> · all
              dashboards
            </p>
            <p>
              exec@etai.com · procure@etai.com · engineer@etai.com · qa@etai.com
            </p>
            <p className="mt-1">
              Password: <span className="text-slate-200">etai123</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
