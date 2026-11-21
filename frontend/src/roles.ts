import { Upload, ScanSearch, Stethoscope } from "lucide-react";
import type { ElementType } from "react";

export type RoleKey = "uploader" | "reviewer" | "doctor";

export const ROLES: Record<RoleKey, {
  label: string; email: string; blurb: string; does: string; Icon: ElementType; home: string;
}> = {
  uploader: {
    label: "Uploader",
    email: "uploader@synth.verilab",
    blurb: "Front desk & lab staff",
    does: "Uploads lab reports for processing.",
    Icon: Upload,
    home: "/",
  },
  reviewer: {
    label: "Reviewer",
    email: "reviewer@synth.verilab",
    blurb: "Quality check",
    does: "Checks extracted values against the original and corrects misreads.",
    Icon: ScanSearch,
    home: "/reports",
  },
  doctor: {
    label: "Doctor",
    email: "doctor@synth.verilab",
    blurb: "Clinician",
    does: "Reads the consultation view, with every result's verification status.",
    Icon: Stethoscope,
    home: "/reports",
  },
};

export const isRoleKey = (r: string): r is RoleKey => r in ROLES;
