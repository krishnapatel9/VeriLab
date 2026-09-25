

interface ConfidenceBadgeProps {
  value: number; // 0–1
}

export function ConfidenceBadge({ value }: ConfidenceBadgeProps) {
  const pct = Math.round(value * 100);
  const isLow = value < 0.9;

  return (
    <span
      className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${
        isLow
          ? "bg-red-100 text-red-700"
          : "bg-green-100 text-green-700"
      }`}
      title={`OCR confidence: ${pct}%`}
    >
      {pct}%
    </span>
  );
}
