import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, FileText, Flag, AlertTriangle } from "lucide-react";
import { getConsultation } from "../api/consultation";
import { getOriginalFile } from "../api/intake";
import { DisclosureBanner } from "../components/DisclosureBanner";
import { VerificationStatusBadge } from "../components/VerificationStatusBadge";
import type { ConsultationResponse, ConsultationResultItem } from "../types";

export default function Consultation() {
  const { reportId } = useParams<{ reportId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<ConsultationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showAdditional, setShowAdditional] = useState(false);

  useEffect(() => {
    if (!reportId) return;
    getConsultation(reportId).then(setData).catch((e: Error) => setError(e.message));
  }, [reportId]);

  const openOriginal = async () => {
    if (!reportId) return;
    const blob = await getOriginalFile(reportId);
    window.open(URL.createObjectURL(blob), "_blank", "noopener");
  };

  if (error) return <p role="alert" className="text-flag">{error}</p>;
  if (!data) {
    return <div className="space-y-4"><div className="skeleton h-10 w-72" /><div className="skeleton h-64" /></div>;
  }

  const flagged = data.selected_results.filter((r) => r.is_critical);

  return (
    <div className="animate-rise space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <button onClick={() => navigate("/reports")} className="mb-3 inline-flex items-center gap-1.5 text-sm text-ink-2 hover:text-ink"><ArrowLeft className="h-4 w-4" />Reports</button>
          <p className="eyebrow">{data.consultation_type} · rules v{data.rule_version}</p>
          <h1 className="mt-1 font-display text-[34px] font-medium tracking-tight">Consultation <span className="num text-[28px]">{data.report_id.slice(0, 8)}</span></h1>
        </div>
        <button onClick={openOriginal} className="btn-quiet"><FileText className="h-4 w-4" />View original</button>
      </div>

      {data.pending_count > 0 && (
        <div role="status" className="flex items-start gap-3 rounded-2xl border border-pending/25 bg-pending-soft px-5 py-4 text-sm text-pending">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <p><span className="font-semibold">{data.pending_count} result{data.pending_count !== 1 ? "s" : ""} not yet verified by a reviewer.</span> They are shown below and marked. Treat them as unconfirmed.</p>
        </div>
      )}

      {flagged.length > 0 && (
        <section aria-label="Flagged on the report" className="rounded-2xl border border-flag/25 bg-flag-soft p-5">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-flag"><Flag className="h-4 w-4" />Flagged on the report ({flagged.length})</h2>
          <ul className="mt-3 grid gap-2 sm:grid-cols-2">
            {flagged.map((r) => (
              <li key={r.id} className="flex items-center justify-between gap-3 rounded-xl bg-surface px-4 py-3 shadow-card">
                <div>
                  <p className="text-sm font-medium">{r.test_name_raw}</p>
                  <p className="num text-sm text-ink-2">{r.value_raw} {r.unit_raw} <span className="text-flag">· {r.flag_raw}</span></p>
                </div>
                <VerificationStatusBadge status={r.verification_status} />
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="card overflow-hidden">
        <div className="flex items-baseline justify-between border-b border-line px-6 py-4">
          <h2 className="font-display text-xl">Results for this consultation</h2>
          <span className="num text-sm text-ink-3">{data.selected_results.length}</span>
        </div>
        {data.selected_results.length === 0 ? (
          <p className="px-6 py-14 text-center text-sm text-ink-2">No results on this report match the consultation’s test list.</p>
        ) : (
          <ResultTable results={data.selected_results} />
        )}
      </section>

      <DisclosureBanner additionalCount={data.additional_results.length} consultationType={data.consultation_type} expanded={showAdditional} onToggle={() => setShowAdditional((v) => !v)} />
      {showAdditional && data.additional_results.length > 0 && (
        <section className="card overflow-hidden">
          <div className="border-b border-line px-6 py-4"><h2 className="font-display text-xl">Other results on the report</h2></div>
          <ResultTable results={data.additional_results} />
        </section>
      )}
    </div>
  );
}

function ResultTable({ results }: { results: ConsultationResultItem[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left">
        <thead>
          <tr className="border-b border-line bg-paper/60">
            {["Test", "Result", "Reference", "Flag", "Verification"].map((h) => (
              <th key={h} className="eyebrow px-6 py-3 font-semibold">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {results.map((r) => (
            <tr key={r.id} className="transition hover:bg-paper/50">
              <td className="px-6 py-4 text-sm font-medium">{r.test_name_raw}</td>
              <td className="px-6 py-4">
                <div className="flex items-baseline gap-1.5">
                  <span className={`num text-lg font-medium ${r.is_critical ? "text-flag" : ""}`}>{r.value_raw}</span>
                  <span className="text-xs text-ink-2">{r.unit_raw}</span>
                </div>
                {r.is_corrected && <p className="num mt-0.5 text-xs text-ink-3">OCR read <span className="line-through">{r.original_value_raw}</span></p>}
              </td>
              <td className="num px-6 py-4 text-sm text-ink-2">{r.reference_range_raw ?? "—"}</td>
              <td className="px-6 py-4">
                {r.flag_raw && r.flag_raw.toLowerCase() !== "normal" ? (
                  <span className="inline-flex items-center gap-1 rounded-full bg-flag-soft px-2.5 py-1 text-xs font-medium text-flag"><Flag className="h-3 w-3" />{r.flag_raw}</span>
                ) : (
                  <span className="text-sm text-ink-3">{r.flag_raw ?? "—"}</span>
                )}
              </td>
              <td className="px-6 py-4"><VerificationStatusBadge status={r.verification_status} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
