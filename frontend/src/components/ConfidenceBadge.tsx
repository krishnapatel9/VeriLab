interface ConfidenceBadgeProps {
  value: number; // 0–1
}

export function ConfidenceBadge({ value }: ConfidenceBadgeProps) {
  const pct = Math.round(value * 100);
  const low = value < 0.9;
  return (
    <span className="inline-flex items-center gap-2 text-sm" title={`OCR confidence: ${pct}%`}>
      <span className="h-1.5 w-14 overflow-hidden rounded-full bg-line">
        <span className={`block h-full rounded-full ${low ? "bg-pending" : "bg-ok"}`} style={{ width: `${pct}%` }} />
      </span>
      <span className={`num ${low ? "font-medium text-pending" : "text-ink-2"}`}>{pct}%{low && " · low"}</span>
    </span>
  );
}
