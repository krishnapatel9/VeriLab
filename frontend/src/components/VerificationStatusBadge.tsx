import React from "react";
import { AlertTriangle, CheckCircle2, CircleDashed, PencilLine } from "lucide-react";
import type { VerificationStatus } from "../types";

const CONFIG: Record<VerificationStatus, { label: string; className: string; Icon: React.ElementType }> = {
  unverified: { label: "Not yet verified", className: "bg-paper text-ink-2 ring-line-strong", Icon: CircleDashed },
  needs_review: { label: "Needs review", className: "bg-pending-soft text-pending ring-pending/25", Icon: AlertTriangle },
  verified_as_reported: { label: "Verified", className: "bg-ok-soft text-ok ring-ok/20", Icon: CheckCircle2 },
  verified_with_correction: { label: "Corrected & verified", className: "bg-fix-soft text-fix ring-fix/20", Icon: PencilLine },
};

/** Text + icon + colour: uncertainty is never conveyed by colour alone. */
export function VerificationStatusBadge({ status }: { status: VerificationStatus }) {
  const { label, className, Icon } = CONFIG[status] ?? CONFIG.unverified;
  return (
    <span className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${className}`}>
      <Icon className="h-3.5 w-3.5" aria-hidden="true" />
      {label}
    </span>
  );
}
