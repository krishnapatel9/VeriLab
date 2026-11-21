import { Layers } from "lucide-react";

interface DisclosureBannerProps {
  additionalCount: number;
  consultationType: string;
  expanded: boolean;
  onToggle: () => void;
}

/** FR-27: tells the doctor that extracted results exist outside this consultation's test list. */
export function DisclosureBanner({ additionalCount, consultationType, expanded, onToggle }: DisclosureBannerProps) {
  if (additionalCount === 0) return null;
  return (
    <div className="flex items-center justify-between gap-4 rounded-2xl border border-line bg-surface px-5 py-4 shadow-card">
      <div className="flex items-start gap-3">
        <Layers className="mt-0.5 h-4 w-4 shrink-0 text-ink-3" aria-hidden="true" />
        <p className="text-sm text-ink-2">
          <span className="font-semibold text-ink">
            {additionalCount} more result{additionalCount !== 1 ? "s" : ""}
          </span>{" "}
          on this report {additionalCount !== 1 ? "are" : "is"} outside the “{consultationType}” list. Nothing has been dropped.
        </p>
      </div>
      <button onClick={onToggle} className="btn-quiet shrink-0 !py-1.5">
        {expanded ? "Hide" : "Show all"}
      </button>
    </div>
  );
}
