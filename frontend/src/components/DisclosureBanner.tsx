
import { AlertCircle } from "lucide-react";

interface DisclosureBannerProps {
  additionalCount: number;
  consultationType: string;
  expanded: boolean;
  onToggle: () => void;
}

/**
 * FR-27 disclosure banner — informs the doctor that additional extracted
 * results exist outside the current consultation's test selection.
 */
export function DisclosureBanner({
  additionalCount,
  consultationType,
  expanded,
  onToggle,
}: DisclosureBannerProps) {
  if (additionalCount === 0) return null;

  return (
    <div className="mt-6 border border-amber-200 bg-amber-50 rounded-lg overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
          <p className="text-sm text-amber-800">
            <span className="font-semibold">{additionalCount} additional result{additionalCount !== 1 ? "s" : ""}</span>{" "}
            extracted from this report are not part of the{" "}
            <span className="font-medium">"{consultationType}"</span> consultation.
            All results are stored and available.
          </p>
        </div>
        <button
          onClick={onToggle}
          className="ml-4 shrink-0 text-xs font-medium text-amber-700 hover:text-amber-900 underline"
        >
          {expanded ? "Hide" : "View all"}
        </button>
      </div>
    </div>
  );
}
