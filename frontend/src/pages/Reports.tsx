import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { FileText, ArrowRight, AlertTriangle, CheckCircle2, Loader2, Inbox } from "lucide-react";
import { getReports } from "../api/intake";
import { useAuth } from "../context/AuthContext";
import type { ReportListItem } from "../types";

const STATUS: Record<string, { label: string; cls: string; icon: React.ReactNode }> = {
  processed: { label: "Ready", cls: "bg-ok-soft text-ok ring-ok/20", icon: <CheckCircle2 className="h-3.5 w-3.5" /> },
  processing: { label: "Reading…", cls: "bg-pending-soft text-pending ring-pending/25", icon: <Loader2 className="h-3.5 w-3.5 animate-spin" /> },
  intake_pending: { label: "Queued", cls: "bg-paper text-ink-2 ring-line-strong", icon: <Loader2 className="h-3.5 w-3.5 animate-spin" /> },
  error: { label: "Failed", cls: "bg-flag-soft text-flag ring-flag/20", icon: <AlertTriangle className="h-3.5 w-3.5" /> },
};

const COPY: Record<string, { title: string; sub: string; action?: string }> = {
  uploader: { title: "Your uploads", sub: "Reports you’ve sent in and where they are." },
  reviewer: { title: "Review queue", sub: "Check the extracted values against the original document." },
  doctor: { title: "Reports", sub: "Open a report to see its results and how far each one has been verified." },
};

export default function Reports() {
  const [reports, setReports] = useState<ReportListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { user } = useAuth();
  const role = user?.role ?? "";
  const copy = COPY[role] ?? { title: "Reports", sub: "" };

  const latest = useRef<ReportListItem[] | null>(null);
  latest.current = reports;

  useEffect(() => {
    let alive = true;
    const load = () =>
      getReports()
        .then((d) => alive && setReports(d.reports))
        .catch((e: Error) => alive && setError(e.message));
    load();
    // Keep polling only while something is still being read.
    const t = setInterval(() => {
      const cur = latest.current;
      if (!cur || cur.some((r) => r.status === "processing" || r.status === "intake_pending")) load();
    }, 3000);
    return () => { alive = false; clearInterval(t); };
  }, []);

  const open = (r: ReportListItem) => navigate(role === "reviewer" ? `/review/${r.id}` : `/consultation/${r.id}`);
  const canOpen = role === "reviewer" || role === "doctor" || role === "admin";

  return (
    <div className="animate-rise">
      <p className="eyebrow">Workspace</p>
      <h1 className="mt-2 font-display text-[34px] font-medium tracking-tight">{copy.title}</h1>
      <p className="mt-1.5 text-[15px] text-ink-2">{copy.sub}</p>

      <div className="card mt-8 overflow-hidden">
        {error ? (
          <p role="alert" className="p-6 text-sm text-flag">{error}</p>
        ) : reports === null ? (
          <div className="divide-y divide-line">
            {[0, 1, 2].map((i) => (
              <div key={i} className="flex items-center gap-4 px-6 py-5">
                <div className="skeleton h-10 w-10" />
                <div className="space-y-2"><div className="skeleton h-3.5 w-40" /><div className="skeleton h-3 w-24" /></div>
              </div>
            ))}
          </div>
        ) : reports.length === 0 ? (
          <div className="px-6 py-20 text-center">
            <Inbox className="mx-auto h-9 w-9 text-ink-3" strokeWidth={1.5} />
            <h3 className="mt-4 font-display text-xl">Nothing here yet</h3>
            <p className="mx-auto mt-1 max-w-sm text-sm text-ink-2">
              {role === "uploader" ? "Upload a lab report and it will show up here." : "Reports appear once an uploader sends one in."}
            </p>
            {role === "uploader" && <button onClick={() => navigate("/")} className="btn-primary mt-6">Upload a report</button>}
          </div>
        ) : (
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-line bg-paper/60">
                <th className="eyebrow px-6 py-3 font-semibold">Report</th>
                <th className="eyebrow hidden px-6 py-3 font-semibold sm:table-cell">Received</th>
                <th className="eyebrow px-6 py-3 font-semibold">Status</th>
                <th className="px-6 py-3"><span className="sr-only">Action</span></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {reports.map((r) => {
                const s = STATUS[r.status] ?? STATUS.intake_pending;
                const ready = r.status === "processed";
                return (
                  <tr key={r.id} className="group transition hover:bg-paper/50">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-4">
                        <span className="grid h-10 w-10 place-items-center rounded-lg bg-brand-soft text-brand"><FileText className="h-[18px] w-[18px]" /></span>
                        <div>
                          <p className="num text-sm font-medium">{r.id.slice(0, 8)}</p>
                          <p className="num text-xs text-ink-3" title={r.file_hash}>sha256 {r.file_hash.slice(0, 10)}…</p>
                        </div>
                      </div>
                    </td>
                    <td className="hidden px-6 py-4 text-sm text-ink-2 sm:table-cell">
                      {new Date(r.created_at).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" })}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${s.cls}`}>{s.icon}{s.label}</span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      {canOpen && (
                        <button onClick={() => open(r)} disabled={!ready} className="btn-quiet !py-1.5 group-hover:border-brand group-hover:text-brand">
                          {role === "reviewer" ? "Review" : "Open"} <ArrowRight className="h-4 w-4" />
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
