import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Loader2, ShieldCheck, Check } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { apiClient } from "../api/client";
import { ROLES, type RoleKey } from "../roles";
import { Wordmark } from "../components/Brand";

// Demo workspace: the password is prefilled in dev builds only.
const DEMO_PASSWORD = import.meta.env.DEV ? "dev123" : "";

export default function Login() {
  const [role, setRole] = useState<RoleKey>("reviewer");
  const [password, setPassword] = useState(DEMO_PASSWORD);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const formData = new URLSearchParams({ username: ROLES[role].email, password });
      const res = await apiClient.post("/api/v1/auth/login", formData, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });
      login(res.data.access_token);
      navigate(ROLES[role].home);
    } catch (err) {
      const message = err instanceof Error ? err.message : "";
      setError(
        message.startsWith("Incorrect")
          ? "That password isn’t right."
          : message.startsWith("Too many")
            ? message
            : "Can’t reach the server. Is the backend running on port 8000?"
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="grid min-h-screen lg:grid-cols-[1.05fr_1fr]">
      {/* Brand panel */}
      <aside className="relative hidden overflow-hidden bg-brand-deep p-14 text-white lg:flex lg:flex-col lg:justify-between">
        <div
          className="absolute inset-0 opacity-[0.07]"
          style={{ backgroundImage: "radial-gradient(circle at 1px 1px, #fff 1px, transparent 0)", backgroundSize: "22px 22px" }}
        />
        <div className="relative">
          <Wordmark light />
        </div>
        <div className="relative max-w-md animate-rise">
          <p className="eyebrow !text-white/50">Lab report review</p>
          <h1 className="mt-4 font-display text-[44px] font-medium leading-[1.08] tracking-tight">
            Every value,
            <br />
            traced to its source.
          </h1>
          <p className="mt-5 text-[15px] leading-relaxed text-white/65">
            Reports are read, checked by a person, then handed to the doctor, with the original, the correction and the audit trail kept side by side.
          </p>

          {/* a specimen row: shows the product idea, not a stock illustration */}
          <div className="mt-10 rounded-xl bg-white/[0.06] p-4 ring-1 ring-white/10 backdrop-blur">
            <div className="flex items-center justify-between text-xs text-white/50">
              <span>Hemoglobin</span>
              <span>p.1 · source linked</span>
            </div>
            <div className="mt-2 flex items-baseline gap-3">
              <span className="num text-sm text-white/40 line-through">12.5</span>
              <span className="num text-2xl font-medium">12.6</span>
              <span className="text-xs text-white/50">g/dL</span>
              <span className="ml-auto inline-flex items-center gap-1 rounded-full bg-white/10 px-2 py-0.5 text-[11px]">
                <Check className="h-3 w-3" />
                Corrected &amp; verified
              </span>
            </div>
          </div>
        </div>
        <p className="relative flex items-center gap-2 text-xs text-white/45">
          <ShieldCheck className="h-4 w-4" /> Synthetic demo data only. Not for clinical use.
        </p>
      </aside>

      {/* Form */}
      <main className="flex items-center justify-center px-6 py-14">
        <form onSubmit={handleLogin} className="w-full max-w-[440px] animate-rise">
          <div className="mb-9 lg:hidden">
            <Wordmark />
          </div>
          <h2 className="font-display text-[32px] font-medium tracking-tight">Sign in</h2>
          <p className="mt-2 text-sm text-ink-2">Choose how you’re working today.</p>

          <fieldset className="mt-7">
            <legend className="sr-only">Role</legend>
            <div className="grid gap-2.5">
              {(Object.keys(ROLES) as RoleKey[]).map((key) => {
                const r = ROLES[key];
                const active = role === key;
                return (
                  <label
                    key={key}
                    className={`group flex cursor-pointer items-center gap-4 rounded-xl border p-4 transition focus-within:ring-2 focus-within:ring-brand ${
                      active ? "border-brand bg-brand-soft/60 shadow-card" : "border-line bg-surface hover:border-line-strong"
                    }`}
                  >
                    <input type="radio" name="role" value={key} checked={active} onChange={() => setRole(key)} className="sr-only" />
                    <span className={`grid h-10 w-10 shrink-0 place-items-center rounded-lg transition ${active ? "bg-brand text-white" : "bg-paper text-ink-2"}`}>
                      <r.Icon className="h-[18px] w-[18px]" />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="flex items-baseline gap-2">
                        <span className="text-[15px] font-semibold">{r.label}</span>
                        <span className="text-xs text-ink-3">{r.blurb}</span>
                      </span>
                      <span className="mt-0.5 block text-[13px] leading-snug text-ink-2">{r.does}</span>
                    </span>
                    <span className={`grid h-5 w-5 shrink-0 place-items-center rounded-full border transition ${active ? "border-brand bg-brand text-white" : "border-line-strong"}`}>
                      {active && <Check className="h-3 w-3" />}
                    </span>
                  </label>
                );
              })}
            </div>
          </fieldset>

          <label className="mt-6 block">
            <span className="text-sm font-medium">Password</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
              className="mt-1.5 w-full rounded-lg border border-line-strong bg-surface px-3.5 py-2.5 text-sm transition placeholder:text-ink-3 focus:border-brand"
            />
          </label>

          {error && (
            <p role="alert" className="mt-4 rounded-lg bg-flag-soft px-3.5 py-2.5 text-sm text-flag">
              {error}
            </p>
          )}

          <button type="submit" disabled={busy} className="btn-primary mt-6 w-full !py-3 text-[15px]">
            {busy ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                Continue as {ROLES[role].label}
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </button>

          {import.meta.env.DEV && (
            <p className="mt-5 text-center text-xs text-ink-3">
              Demo workspace · <span className="num">SYNTH-Clinic-001</span> · password <span className="num">dev123</span>
            </p>
          )}
        </form>
      </main>
    </div>
  );
}
