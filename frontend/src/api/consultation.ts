import { apiClient } from "./client";
import type { ConsultationResponse } from "../types";

/**
 * Fetch the doctor consultation view for a given report.
 * Returns selected results (per consultation type) and additional results (FR-27).
 */
export async function getConsultation(
  reportId: string
): Promise<ConsultationResponse> {
  const response = await apiClient.get<ConsultationResponse>(
    `/api/v1/consultation/${reportId}`
  );
  return response.data;
}
