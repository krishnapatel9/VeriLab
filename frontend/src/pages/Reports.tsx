import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { FileText, ArrowRight, Clock, AlertTriangle, CheckCircle } from "lucide-react";
import { getReports } from "../api/intake";
import { useAuth } from "../context/AuthContext";
import type { ReportListItem } from "../types";

export default function Reports() {
  const [reports, setReports] = useState<ReportListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { user } = useAuth();

  useEffect(() => {
    async function loadReports() {
      try {
        const data = await getReports();
        setReports(data.reports);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    loadReports();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-slate-500 font-medium">Loading reports...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-slate-900">Lab Reports</h1>
      </div>

      {reports.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border border-slate-200 shadow-sm">
          <FileText className="mx-auto h-12 w-12 text-slate-400" />
          <h3 className="mt-2 text-sm font-semibold text-slate-900">No reports</h3>
          <p className="mt-1 text-sm text-slate-500">No lab reports have been processed yet.</p>
        </div>
      ) : (
        <div className="bg-white shadow-sm ring-1 ring-slate-200 rounded-lg overflow-hidden">
          <ul className="divide-y divide-slate-200">
            {reports.map((report) => (
              <li key={report.id}>
                <div className="p-4 sm:px-6 hover:bg-slate-50 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="bg-blue-50 p-2 rounded-lg">
                        <FileText className="w-6 h-6 text-blue-600" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-slate-900 font-mono">
                          {report.id.split("-")[0]}...
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          <Clock className="w-3 h-3 text-slate-400" />
                          <span className="text-xs text-slate-500">
                            {new Date(report.created_at).toLocaleString()}
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-6">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium capitalize border ${
                        report.status === 'processed' ? 'bg-green-50 text-green-700 border-green-200' :
                        report.status === 'processing' ? 'bg-yellow-50 text-yellow-700 border-yellow-200' :
                        report.status === 'error' ? 'bg-red-50 text-red-700 border-red-200' :
                        'bg-slate-50 text-slate-700 border-slate-200'
                      }`}>
                        {report.status === 'processed' && <CheckCircle className="w-3.5 h-3.5" />}
                        {report.status === 'error' && <AlertTriangle className="w-3.5 h-3.5" />}
                        {report.status}
                      </span>

                      <button
                        onClick={() => navigate(user?.role === "reviewer" ? `/review/${report.id}` : `/consultation/${report.id}`)}
                        className="inline-flex items-center gap-1 text-sm font-medium text-blue-600 hover:text-blue-800"
                        disabled={report.status !== 'processed'}
                      >
                        {user?.role === "reviewer" ? "Review" : "Consultation"}
                        <ArrowRight className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
