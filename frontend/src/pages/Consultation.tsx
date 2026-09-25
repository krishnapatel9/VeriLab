import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Activity, ArrowLeft, FileText, CheckCircle, AlertCircle, ShieldCheck
} from 'lucide-react';
import { getConsultation } from '../api/consultation';
import { DisclosureBanner } from '../components/DisclosureBanner';
import type { ConsultationResponse, ConsultationResultItem } from '../types';

export default function Consultation() {
  const { reportId } = useParams<{ reportId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<ConsultationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAdditional, setShowAdditional] = useState(false);

  useEffect(() => {
    if (!reportId) return;
    getConsultation(reportId)
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [reportId]);

  if (loading) return <div className="p-8 text-center text-slate-500">Loading consultation view...</div>;
  if (error) {
    return (
      <div className="p-8 text-center">
        <div className="text-red-500 mb-2">Error: {error}</div>
        {error.includes('404') && (
          <p className="text-sm text-slate-500">
            The report may still be processing. Go back to the Review page and ensure all results are verified first.
          </p>
        )}
      </div>
    );
  }
  if (!data) return null;

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate(-1)} className="text-slate-500 hover:text-slate-900">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <Activity className="w-6 h-6 text-blue-600" />
            <h1 className="text-xl font-semibold text-slate-900">Doctor Consultation View</h1>
          </div>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <span className="text-slate-500">Consultation type:</span>
          <span className="font-medium text-slate-700">{data.consultation_type}</span>
          <span className="text-slate-300">|</span>
          <span className="text-slate-500">Rules v{data.rule_version}</span>
        </div>
      </header>

      <main className="max-w-5xl mx-auto p-6 space-y-6">
        {/* Report info bar */}
        <div className="bg-white rounded-xl border border-slate-200 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-slate-400" />
            <span className="text-sm text-slate-600">Report status:</span>
            <span className="text-sm font-medium text-slate-900 capitalize">{data.report_status}</span>
          </div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-green-500" />
            <span className="text-xs text-slate-500">
              Showing only clinically reviewed, verified results
            </span>
          </div>
        </div>

        {/* Selected results table */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">
              Selected Test Results
              <span className="ml-2 text-sm font-normal text-slate-500">({data.selected_results.length})</span>
            </h2>
          </div>

          {data.selected_results.length === 0 ? (
            <div className="p-8 text-center text-slate-500">
              <AlertCircle className="w-8 h-8 mx-auto mb-2 text-slate-300" />
              <p>No verified results available for this consultation type yet.</p>
              <p className="text-sm mt-1">Return to the Review page to verify extracted results.</p>
              <button
                onClick={() => navigate(`/review/${reportId}`)}
                className="mt-4 text-sm text-blue-600 underline"
              >
                Go to Review
              </button>
            </div>
          ) : (
            <ResultTable results={data.selected_results} />
          )}
        </div>

        {/* FR-27: Additional results disclosure */}
        <DisclosureBanner
          additionalCount={data.additional_results.length}
          consultationType={data.consultation_type}
          expanded={showAdditional}
          onToggle={() => setShowAdditional((v) => !v)}
        />
        {showAdditional && data.additional_results.length > 0 && (
          <div className="bg-white rounded-xl border border-amber-200 overflow-hidden">
            <div className="px-6 py-3 bg-amber-50 border-b border-amber-200">
              <h3 className="text-sm font-semibold text-amber-900">
                Additional Extracted Results (not in this consultation)
              </h3>
            </div>
            <ResultTable results={data.additional_results} dimmed />
          </div>
        )}

        <div className="flex justify-end">
          <p className="text-xs text-slate-400 flex items-center gap-1">
            <CheckCircle className="w-3 h-3" />
            All data presented has been extracted and clinically verified.
          </p>
        </div>
      </main>
    </div>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function ResultTable({
  results,
  dimmed = false,
}: {
  results: ConsultationResultItem[];
  dimmed?: boolean;
}) {
  return (
    <table className={`w-full text-left ${dimmed ? 'opacity-75' : ''}`}>
      <thead className="bg-slate-50/50">
        <tr>
          <th className="px-6 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Test</th>
          <th className="px-6 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Result</th>
          <th className="px-6 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Reference</th>
          <th className="px-6 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Flag</th>
          <th className="px-6 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Status</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-slate-100">
        {results.map((item) => {
          const isAbnormal = item.flag_raw && item.flag_raw.toLowerCase() !== 'normal';
          return (
            <tr key={item.id} className="hover:bg-slate-50 transition-colors">
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-slate-900">{item.test_name_raw}</span>
                  {item.is_critical && (
                    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-bold bg-red-600 text-white">
                      CRITICAL
                    </span>
                  )}
                  {item.verification_status === 'verified_with_correction' && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                      Corrected
                    </span>
                  )}
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className={`font-semibold ${isAbnormal ? 'text-red-600' : 'text-slate-900'}`}>
                  {item.value_raw}{' '}
                  <span className="text-slate-500 font-normal text-sm">{item.unit_raw}</span>
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                {item.reference_range_raw ?? '—'}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                {isAbnormal ? (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                    <AlertCircle className="w-3 h-3" /> {item.flag_raw}
                  </span>
                ) : (
                  <span className="text-sm text-slate-400">—</span>
                )}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className="inline-flex items-center gap-1 text-xs font-medium text-green-800 bg-green-100 px-2 py-0.5 rounded-full">
                  <CheckCircle className="w-3 h-3" />
                  {item.verification_status === 'verified_with_correction' ? 'Verified (corrected)' : 'Verified'}
                </span>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

