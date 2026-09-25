import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, FileText, CheckCircle, AlertCircle, ArrowRight, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { uploadReport } from '../api/intake';
import type { UploadResponse } from '../types';

export default function Intake() {
  const { user, logout } = useAuth();
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setError(null);
      setUploadResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    setError(null);

    try {
      const data = await uploadReport(file);
      setUploadResult(data);
    } catch (err: any) {
      setError(err.message || 'An error occurred during upload.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between shadow-sm">
        <h1 className="text-lg font-semibold text-slate-900">Verilab</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-slate-500">
            {user?.role && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 mr-2">
                {user.role}
              </span>
            )}
            {user?.sub?.slice(0, 8)}…
          </span>
          <button
            onClick={logout}
            className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-900"
          >
            <LogOut className="w-4 h-4" /> Logout
          </button>
        </div>
      </header>

      <div className="max-w-4xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-10">
          <h2 className="text-3xl font-bold tracking-tight text-slate-900">Lab Report Intake</h2>
          <p className="mt-2 text-sm text-slate-500">Upload a lab report PDF or image to begin OCR processing.</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8 max-w-2xl mx-auto">
          <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
            <UploadCloud className="w-5 h-5 text-blue-600" />
            Upload Lab Report
          </h3>

          <div className="mt-2 border-2 border-dashed border-slate-300 rounded-lg p-10 flex flex-col items-center justify-center hover:bg-slate-50 transition-colors">
            <input
              type="file"
              id="file-upload"
              className="hidden"
              accept=".pdf,.png,.jpg,.jpeg"
              onChange={handleFileChange}
            />
            <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
              <UploadCloud className="w-12 h-12 text-slate-400 mb-3" />
              <span className="text-sm font-medium text-blue-600">Click to upload</span>
              <span className="text-xs text-slate-400 mt-1">PDF, PNG, JPG up to 10MB</span>
            </label>
          </div>

          {file && (
            <div className="mt-6 flex items-center justify-between p-4 bg-slate-50 rounded-md border border-slate-200">
              <div className="flex items-center gap-3">
                <FileText className="w-8 h-8 text-slate-400" />
                <div>
                  <p className="text-sm font-medium text-slate-900">{file.name}</p>
                  <p className="text-xs text-slate-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              </div>
              <button
                onClick={handleUpload}
                disabled={isUploading}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isUploading ? 'Uploading…' : 'Upload File'}
              </button>
            </div>
          )}

          {error && (
            <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-md flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
              <div className="text-sm text-red-800">{error}</div>
            </div>
          )}

          {uploadResult && (
            <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-md">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <h4 className="text-sm font-medium text-green-900">Upload Successful</h4>
                </div>
                {(user?.role === 'reviewer' || user?.role === 'admin') && (
                  <button
                    onClick={() => navigate(`/review/${uploadResult.report_id}`)}
                    className="flex items-center gap-1 text-sm font-medium text-blue-700 bg-blue-100 hover:bg-blue-200 px-3 py-1.5 rounded transition-colors"
                  >
                    Go to Review <ArrowRight className="w-4 h-4" />
                  </button>
                )}
              </div>
              <div className="bg-white p-3 rounded border border-green-100 text-xs font-mono text-slate-700 overflow-x-auto space-y-1">
                <p><span className="font-semibold">Report ID:</span> {uploadResult.report_id}</p>
                <p><span className="font-semibold">File Hash:</span> {uploadResult.file_hash}</p>
                <p><span className="font-semibold">Status:</span> {uploadResult.status}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
