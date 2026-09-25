import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AlertTriangle, CheckCircle, ArrowLeft, X, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { getReportForReview, verifyResult, correctResult } from '../api/review';
import type { ReportReviewResponse, ResultItem } from '../types';

export default function Review() {
  const { reportId } = useParams<{ reportId: string }>();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const [reportData, setReportData] = useState<ReportReviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Correction Modal State
  const [editingResult, setEditingResult] = useState<ResultItem | null>(null);
  const [correctedValue, setCorrectedValue] = useState('');
  const [correctionReason, setCorrectionReason] = useState('OCR misread');

  const fetchReport = async () => {
    if (!reportId) return;
    try {
      const data = await getReportForReview(reportId);
      setReportData(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, [reportId]);

  const handleVerify = async (resultId: string) => {
    try {
      await verifyResult(resultId, {});
      await fetchReport();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleCorrect = async () => {
    if (!editingResult || !correctedValue) return;
    try {
      await correctResult(editingResult.id, {
        corrected_value_raw: correctedValue,
        reason: correctionReason,
      });
      setEditingResult(null);
      await fetchReport();
    } catch (err: any) {
      alert(err.message);
    }
  };

  if (loading) return <div className="p-8 text-center text-slate-500">Loading report data…</div>;
  if (error) return <div className="p-8 text-center text-red-500">Error: {error}</div>;
  if (!reportData) return null;

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col relative">
      {/* Correction Modal */}
      {editingResult && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 flex justify-between items-center">
              <h3 className="font-semibold text-slate-900">Correct Value</h3>
              <button onClick={() => setEditingResult(null)} className="text-slate-400 hover:text-slate-700">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Test Name</label>
                <div className="p-2 bg-slate-100 rounded text-slate-700 text-sm">{editingResult.test_name_raw}</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Original OCR Value</label>
                <div className="p-2 bg-red-50 text-red-700 rounded text-sm line-through">{editingResult.value_raw}</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Corrected Value</label>
                <input
                  type="text"
                  value={correctedValue}
                  onChange={(e) => setCorrectedValue(e.target.value)}
                  className="w-full border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  autoFocus
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Reason for change</label>
                <select
                  value={correctionReason}
                  onChange={(e) => setCorrectionReason(e.target.value)}
                  className="w-full border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="OCR misread">OCR misread</option>
                  <option value="Typo in original report">Typo in original report</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>
            <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex justify-end gap-3">
              <button onClick={() => setEditingResult(null)} className="px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-200 rounded">
                Cancel
              </button>
              <button onClick={handleCorrect} className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded">
                Save Correction
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate('/')} className="text-slate-500 hover:text-slate-900">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="text-xl font-semibold text-slate-900">Clinical Review</h1>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <span>Status:</span>
            <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-md font-medium capitalize">
              {reportData.status}
            </span>
          </div>
          <button
            onClick={() => navigate(`/consultation/${reportId}`)}
            className="px-4 py-2 bg-slate-900 text-white text-sm font-medium rounded-md hover:bg-slate-800 transition-colors"
          >
            Go to Consultation
          </button>
          <span className="text-sm text-slate-500">
            {user?.role && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 mr-2">
                {user.role}
              </span>
            )}
          </span>
          <button onClick={logout} className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-900">
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </header>

      <main className="flex-1 flex overflow-hidden">
        {/* Left: Mock PDF Viewer */}
        <div className="w-1/2 border-r border-slate-200 bg-slate-100 p-6 overflow-y-auto flex items-center justify-center">
          <div className="bg-white w-full max-w-lg aspect-[8.5/11] shadow-md border border-slate-300 p-8 flex flex-col">
            <h2 className="text-2xl font-bold mb-6 text-center border-b pb-4">LABORATORY REPORT</h2>
            <div className="space-y-4 font-mono text-sm">
              <p>Patient Name: Jane Doe</p>
              <p>Collection Date: 2026-10-01</p>
              <div className="mt-8 border-t pt-4">
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-b">
                      <th className="py-2">Test</th>
                      <th className="py-2">Result</th>
                      <th className="py-2">Unit</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-b">
                      <td className="py-2">Hemoglobin</td>
                      <td className="py-2">12.5</td>
                      <td className="py-2">g/dL</td>
                    </tr>
                    <tr className="border-b bg-yellow-50">
                      <td className="py-2">TSH</td>
                      <td className="py-2 font-bold text-red-600">&lt;0.01</td>
                      <td className="py-2">uIU/mL</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div className="mt-auto text-center text-slate-400 text-xs italic">(Mock PDF Renderer)</div>
          </div>
        </div>

        {/* Right: Data Extraction & Review */}
        <div className="w-1/2 bg-white p-6 overflow-y-auto">
          <h2 className="text-lg font-semibold text-slate-900 mb-6">Extracted Data</h2>

          <div className="space-y-4">
            {reportData.results.map((item: ResultItem) => {
              const isNeedsReview = item.verification_status === 'needs_review';
              const isCorrected = item.verification_status === 'verified_with_correction';
              const isVerified = item.verification_status === 'verified_as_reported';
              const isActionable = !isVerified && !isCorrected;

              return (
                <div
                  key={item.id}
                  className={`p-4 rounded-lg border ${
                    isNeedsReview ? 'border-yellow-300 bg-yellow-50' :
                    isCorrected   ? 'border-blue-300 bg-blue-50' :
                    isVerified    ? 'border-green-300 bg-green-50' :
                    'border-slate-200 bg-white'
                  }`}
                >
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="font-medium text-slate-900">{item.test_name_raw}</h3>
                    {isNeedsReview && (
                      <span className="flex items-center gap-1 text-xs font-medium text-yellow-800 bg-yellow-100 px-2 py-1 rounded">
                        <AlertTriangle className="w-3 h-3" /> Needs Review
                      </span>
                    )}
                    {isVerified && (
                      <span className="flex items-center gap-1 text-xs font-medium text-green-800 bg-green-100 px-2 py-1 rounded">
                        <CheckCircle className="w-3 h-3" /> Verified
                      </span>
                    )}
                    {isCorrected && (
                      <span className="flex items-center gap-1 text-xs font-medium text-blue-800 bg-blue-100 px-2 py-1 rounded">
                        <CheckCircle className="w-3 h-3" /> Corrected
                      </span>
                    )}
                    {!isNeedsReview && !isVerified && !isCorrected && (
                      <span className="flex items-center gap-1 text-xs font-medium text-slate-600 bg-slate-100 px-2 py-1 rounded">
                        Unverified
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-slate-500 block text-xs">Value</span>
                      <span className="font-medium">{item.value_raw} {item.unit_raw}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-xs">Reference Range</span>
                      <span>{item.reference_range_raw ?? '—'}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-xs">Flag</span>
                      <span>{item.flag_raw || '—'}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-xs">Confidence</span>
                      <span className={item.confidence_value < 0.9 ? 'text-red-600 font-medium' : 'text-green-600'}>
                        {(item.confidence_value * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>

                  {isActionable && (
                    <div className="mt-4 pt-4 border-t border-slate-200 flex justify-end gap-2">
                      <button
                        onClick={() => {
                          setEditingResult(item);
                          setCorrectedValue(item.value_raw);
                        }}
                        className="px-3 py-1.5 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded hover:bg-slate-50"
                      >
                        Edit &amp; Correct
                      </button>
                      <button
                        onClick={() => handleVerify(item.id)}
                        className="px-3 py-1.5 text-sm font-medium text-white bg-blue-600 rounded hover:bg-blue-700"
                      >
                        Verify as Reported
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </main>
    </div>
  );
}
