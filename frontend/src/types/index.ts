// Verilab — shared TypeScript type definitions
// These mirror the backend Pydantic schemas exactly.

export type VerificationStatus =
  | "unverified"
  | "needs_review"
  | "verified_as_reported"
  | "verified_with_correction";

export type ReportStatus =
  | "intake_pending"
  | "processing"
  | "processed"
  | "error";

export type ReviewItemStatus = "open" | "resolved";

// ── Intake ──────────────────────────────────────────────────────────────────

export interface UploadResponse {
  report_id: string;
  file_hash: string;
  status: string;
  message: string;
}

export interface ReportListItem {
  id: string;
  file_hash: string;
  status: string;
  created_at: string;
}

export interface ReportListResponse {
  reports: ReportListItem[];
}


// ── Review ───────────────────────────────────────────────────────────────────

export interface ResultItem {
  id: string;
  test_name_raw: string;
  value_raw: string;
  unit_raw: string | null;
  reference_range_raw: string | null;
  flag_raw: string | null;
  confidence_value: number;
  source_page: number;
  source_x: number;
  source_y: number;
  source_width: number;
  source_height: number;
  verification_status: VerificationStatus;
  is_critical: boolean;
}

export interface ReviewItem {
  id: string;
  result_id: string | null;
  item_type: string;
  flag_reason: string;
  status: ReviewItemStatus;
}

export interface ReportReviewResponse {
  id: string;
  file_hash: string;
  status: ReportStatus;
  created_at: string;
  results: ResultItem[];
  review_items: ReviewItem[];
}

export interface VerifyResultRequest {
  reviewer_user_id?: string;
}

export interface CorrectResultRequest {
  reviewer_user_id?: string;
  corrected_value_raw: string;
  reason: string;
  comment?: string;
}

// ── Consultation ──────────────────────────────────────────────────────────────

export interface ConsultationResultItem {
  id: string;
  test_name_raw: string;
  value_raw: string;
  unit_raw: string | null;
  reference_range_raw: string | null;
  flag_raw: string | null;
  is_critical: boolean;
  verification_status: VerificationStatus;
  source_page: number;
  source_x: number;
  source_y: number;
  source_width: number;
  source_height: number;
}

export interface ConsultationResponse {
  report_id: string;
  report_status: ReportStatus;
  rule_version: number;
  consultation_type: string;
  selected_results: ConsultationResultItem[];
  additional_results: ConsultationResultItem[];
}
