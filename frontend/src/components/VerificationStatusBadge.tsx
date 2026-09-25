import React from "react";
import { AlertTriangle, CheckCircle } from "lucide-react";
import type { VerificationStatus } from "../types";

interface Props {
  status: VerificationStatus;
}

const CONFIG: Record<
  VerificationStatus,
  { label: string; className: string; Icon: React.ElementType }
> = {
  unverified: {
    label: "Unverified",
    className: "bg-slate-100 text-slate-600",
    Icon: CheckCircle,
  },
  needs_review: {
    label: "Needs Review",
    className: "bg-yellow-100 text-yellow-800",
    Icon: AlertTriangle,
  },
  verified_as_reported: {
    label: "Verified",
    className: "bg-green-100 text-green-800",
    Icon: CheckCircle,
  },
  verified_with_correction: {
    label: "Corrected",
    className: "bg-blue-100 text-blue-800",
    Icon: CheckCircle,
  },
};

export function VerificationStatusBadge({ status }: Props) {
  const { label, className, Icon } = CONFIG[status] ?? CONFIG.unverified;
  return (
    <span
      className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${className}`}
    >
      <Icon className="w-3 h-3" />
      {label}
    </span>
  );
}
