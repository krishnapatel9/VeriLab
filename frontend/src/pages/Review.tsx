import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, X, Loader2, Flag, FileWarning } from "lucide-react";
import { getReportForReview, verifyResult, correctResult } from "../api/review";
import { getOriginalFile } from "../api/intake";
import { VerificationStatusBadge } from "../components/VerificationStatusBadge";
import { ConfidenceBadge } from "../components/ConfidenceBadge";
import type { ReportReviewResponse, ResultItem } from "../types";

const REASONS = ["OCR misread", "Typo in original report", "Other"];
const isDone = (s: string) => s === "verified_as_reported" || s === "verified_with_correction";

export default function Review() {
  const { reportId } = useParams<{ reportId: string }>();
  const navigate = useNavigate();

  const [data, setData] = useState<ReportReviewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const [editing, setEditing] = useState<ResultItem | null>(null);
  const [value, setValue] = useState("");
  const [reason, setReason] = useState(REASONS[0]);

  // Original document (FR-29): fetched with auth, shown from a blob URL.
  const [doc, setDoc] = useState<{ url: string; type: string } | null>(null);
  const [docError, setDocError] = useState(false);

  const load = async () => {
    if (!reportId) return;
    try {
      setData(await getReportForReview(reportId));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load report");
    }
  };

  useEffect(() => { load(); }, [reportId]);

  useEffect(() => {
    if (!reportId) return;
    let url: string | null = null;
    getOriginalFile(reportId)
      .then((b) => { url = URL.createObjectURL(b); setDoc({ url, type: b.type }); })
      .catch(() => setDocError(true));
    return () => { if (url) URL.revokeObjectURL(url); };
  }, [reportId]);

  const fail = (e: unknown) => {
    setToast(e instanceof Error ? e.message : "Something went wrong");
    setTimeout(() => setToast(null), 4000);
  };

  const verify = async (id: string) => {
    setBusyId(id);
    try { await verifyResult(id, {}); await load(); } catch (e) { fail(e); } finally { setBusyId(null); }
  };

  const saveCorrection = async () => {
    if (!editing || !value.trim()) return;
    setBusyId(editing.id);
    try {
      await correctResult(editing.id, { corrected_value_raw: value.trim(), reason });
      setEditing(null);
      await load();
    } catch (e) { fail(e); } finally { setBusyId(null); }
  };

  if (error) return <p role="alert" className="text-flag">{error}</p>;
  if (!data) {
    return <div className="grid gap-6 lg:grid-cols-2"><div className="skeleton h-[70vh]" /><div className="skeleton h-[70vh]" /></div>;
  }

  const total = data.results.length;
  const done = data.results.filter((r) => isDone(r.verification_status)).length;

  return (
    <div className="animate-rise">
      {toast && <div role="alert" className="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 rounded-lg bg-ink px-4 py-2.5 text-sm text-white shadow-lift">{toast}</div>}

      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <button onClick={() => navigate("/reports")} className="mb-3 inline-flex items-center gap-1.5 text-sm text-ink-2 hover:text-ink"><ArrowLeft className="h-4 w-4" />Review queue</button>
          <p className="eyebrow">Reviewing</p>
          <h1 className="mt-1 font-display text-[30px] font-medium tracking-tight">Report <span className="num text-[26px]">{data.id.slice(0, 8)}</span></h1>
        </div>
        <div className="w-full max-w-xs">
          <div className="flex justify-between text-sm"><span className="text-ink-2">Verified</span><span className="num font-medium">{done} / {total}</span></div>
          <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-line"><div className="h-full rounded-full bg-brand transition-all duration-500" style={{ width: total ? `${(done / total) * 100}%` : 0 }} /></div>
        </div>
      </div>

      <div className="mt-8 grid items-start gap-6 lg:grid-cols-2">
        {/* Original document */}
        <section className="card overflow-hidden lg:sticky lg:top-24">
          <div className="flex items-center justify-between border-b border-line px-5 py-3">
            <h2 className="text-sm font-semibold">Original document</h2>
            <span className="num text-xs text-ink-3" title={data.file_hash}>sha256 {data.file_hash.slice(0, 10)}…</span>
          </div>
          <div className="h-[68vh] bg-paper">
            {docError ? (
              <div className="grid h-full place-items-center p-8 text-center text-sm text-ink-2"><div><FileWarning className="mx-auto mb-3 h-8 w-8 text-ink-3" strokeWidth={1.5} />The original could not be loaded.</div></div>
            ) : !doc ? (
              <div className="skeleton h-full rounded-none" />
            ) : doc.type.startsWith("image/") ? (
              <img src={doc.url} alt="Original lab report" className="h-full w-full object-contain" />
            ) : (
              <iframe src={doc.url} title="Original lab report" className="h-full w-full" />
            )}
          </div>
        </section>

        {/* Extracted results */}
        <section className="space-y-4">
          {data.results.length === 0 && <div className="card p-8 text-center text-sm text-ink-2">No results were extracted from this report.</div>}
          {data.results.map((item) => {
            const done = isDone(item.verification_status);
            const busy = busyId === item.id;
            return (
              <article key={item.id} className={`card p-5 transition ${item.verification_status === "needs_review" ? "ring-2 ring-pending/30" : ""}`}>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="text-[15px] font-semibold">{item.test_name_raw}</h3>
                    {item.is_critical && (
                      <span className="mt-1.5 inline-flex items-center gap-1 rounded-full bg-flag-soft px-2 py-0.5 text-xs font-medium text-flag"><Flag className="h-3 w-3" />Flagged on report: {item.flag_raw}</span>
                    )}
                  </div>
                  <VerificationStatusBadge status={item.verification_status} />
                </div>

                <div className="mt-4 flex items-baseline gap-2">
                  <span className="num text-[28px] font-medium leading-none">{item.value_raw}</span>
                  <span className="text-sm text-ink-2">{item.unit_raw}</span>
                </div>

                <dl className="mt-4 grid grid-cols-3 gap-4 border-t border-line pt-4 text-sm">
                  <div><dt className="eyebrow">Reference</dt><dd className="num mt-1 text-ink-2">{item.reference_range_raw ?? "—"}</dd></div>
                  <div><dt className="eyebrow">Confidence</dt><dd className="mt-1"><ConfidenceBadge value={item.confidence_value ?? 0} /></dd></div>
                  <div><dt className="eyebrow">Source</dt><dd className="num mt-1 text-ink-2">p.{item.source_page} · {Math.round(item.source_x)},{Math.round(item.source_y)}</dd></div>
                </dl>

                {!done && (
                  <div className="mt-5 flex justify-end gap-2">
                    <button onClick={() => { setEditing(item); setValue(item.value_raw); setReason(REASONS[0]); }} className="btn-quiet">Correct</button>
                    <button onClick={() => verify(item.id)} disabled={busy} className="btn-primary">
                      {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : "Matches the original"}
                    </button>
                  </div>
                )}
              </article>
            );
          })}
        </section>
      </div>

      {/* Correction dialog */}
      {editing && (
        <div className="fixed inset-0 z-40 grid place-items-center bg-ink/40 p-4 backdrop-blur-sm" onClick={() => setEditing(null)}>
          <div role="dialog" aria-modal="true" aria-label="Correct value" className="card w-full max-w-md animate-rise shadow-lift" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between border-b border-line px-6 py-4">
              <h3 className="font-display text-xl">Correct {editing.test_name_raw}</h3>
              <button onClick={() => setEditing(null)} className="text-ink-3 hover:text-ink" aria-label="Close"><X className="h-5 w-5" /></button>
            </div>
            <div className="space-y-5 p-6">
              <div>
                <p className="eyebrow">As read by OCR (kept on record)</p>
                <p className="num mt-1.5 rounded-lg bg-paper px-3 py-2 text-sm text-ink-2 line-through decoration-flag/60">{editing.value_raw}</p>
              </div>
              <label className="block">
                <span className="text-sm font-medium">Value on the original document</span>
                <input value={value} onChange={(e) => setValue(e.target.value)} autoFocus className="num mt-1.5 w-full rounded-lg border border-line-strong px-3.5 py-2.5 text-sm focus:border-brand" />
              </label>
              <label className="block">
                <span className="text-sm font-medium">Reason</span>
                <select value={reason} onChange={(e) => setReason(e.target.value)} className="mt-1.5 w-full rounded-lg border border-line-strong bg-surface px-3.5 py-2.5 text-sm focus:border-brand">
                  {REASONS.map((r) => <option key={r}>{r}</option>)}
                </select>
              </label>
            </div>
            <div className="flex justify-end gap-2 border-t border-line bg-paper/60 px-6 py-4">
              <button onClick={() => setEditing(null)} className="btn-quiet">Cancel</button>
              <button onClick={saveCorrection} disabled={!value.trim() || busyId === editing.id} className="btn-primary">Save correction</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
