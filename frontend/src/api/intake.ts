import { apiClient } from "./client";
import type { UploadResponse, ReportListResponse } from "../types";

export async function getReports(): Promise<ReportListResponse> {
  const response = await apiClient.get<ReportListResponse>("/api/v1/intake/reports");
  return response.data;
}

/**
 * Upload a lab report file (PDF, PNG, JPG, JPEG).
 * Returns the report_id to pass to the review and consultation endpoints.
 */
export async function uploadReport(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post<UploadResponse>(
    "/api/v1/intake/upload",
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return response.data;
}
