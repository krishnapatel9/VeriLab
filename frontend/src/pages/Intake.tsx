import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { UploadCloud, FileText, CheckCircle2, AlertCircle, ArrowRight, Loader2, X } from "lucide-react";
import { uploadReport } from "../api/intake";
import type { UploadResponse } from "../types";

export default function Intake() {
  const [file, setFile] = useState<File | null>(null);
  const [drag, setDrag] = useState(false);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<UploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const pick = (f: File | undefined) => {
    if (!f) return;
    setFile(f);
    setError(null);
    setResult(null);
  };

  const upload = async () => {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      setResult(await uploadReport(file));
      setFile(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl animate-rise">
      <p className="eyebrow">Intake</p>
      <h1 className="mt-2 font-display text-[34px] font-medium tracking-tight">Upload a lab report</h1>
      <p className="mt-1.5 text-[15px] text-ink-2">
        The original is hashed and stored untouched. A reviewer checks what we read from it before a doctor sees anything.
      </p>

      <div className="card mt-8 p-2">
        <label
          htmlFor="file-upload"
          onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => { e.preventDefault(); setDrag(false); pick(e.dataTransfer.files[0]); }}
          className={`flex cursor-pointer flex-col items-center rounded-xl border-2 border-dashed px-6 py-14 text-center transition ${
            drag ? "border-brand bg-brand-soft/60" : "border-line-strong hover:border-brand hover:bg-paper/60"
          }`}
        >
          <input id="file-upload" type="file" className="sr-only" accept=".pdf,.png,.jpg,.jpeg" onChange={(e) => pick(e.target.files?.[0])} />
          <span className="grid h-12 w-12 place-items-center rounded-full bg-brand-soft text-brand"><UploadCloud className="h-6 w-6" /></span>
          <span className="mt-4 text-[15px] font-medium">Drop a file here, or <span className="text-brand underline underline-offset-4">browse</span></span>
          <span className="mt-1 text-xs text-ink-3">PDF, PNG or JPG · up to 10 MB</span>
        </label>
      </div>

      {file && (
        <div className="card mt-4 flex items-center gap-4 p-4 animate-rise">
          <span className="grid h-11 w-11 place-items-center rounded-lg bg-paper text-ink-2"><FileText className="h-5 w-5" /></span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{file.name}</p>
            <p className="num text-xs text-ink-3">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
          </div>
          <button onClick={() => setFile(null)} className="btn-quiet !border-transparent !px-2" aria-label="Remove file"><X className="h-4 w-4" /></button>
          <button onClick={upload} disabled={busy} className="btn-primary">
            {busy ? <><Loader2 className="h-4 w-4 animate-spin" />Uploading…</> : "Upload"}
          </button>
        </div>
      )}

      {error && (
        <div role="alert" className="mt-4 flex items-start gap-3 rounded-xl bg-flag-soft p-4 text-sm text-flag">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />{error}
        </div>
      )}

      {result && (
        <div className="card mt-4 p-5 animate-rise">
          <div className="flex items-center gap-2 text-ok">
            <CheckCircle2 className="h-5 w-5" />
            <h3 className="text-[15px] font-semibold">Received. Reading it now.</h3>
          </div>
          <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-[110px_1fr]">
            <dt className="text-ink-3">Report</dt><dd className="num">{result.report_id}</dd>
            <dt className="text-ink-3">SHA-256</dt><dd className="num break-all text-ink-2">{result.file_hash}</dd>
          </dl>
          <button onClick={() => navigate("/reports")} className="btn-quiet mt-5">Track it in Reports <ArrowRight className="h-4 w-4" /></button>
        </div>
      )}
    </div>
  );
}
