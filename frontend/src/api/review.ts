import { apiClient } from "./client";
import type {
  ReportReviewResponse,
  VerifyResultRequest,
  CorrectResultRequest,
} from "../types";

export async function getReportForReview(
  reportId: string
): Promise<ReportReviewResponse> {
  const response = await apiClient.get<ReportReviewResponse>(
    `/api/v1/review/reports/${reportId}`
  );
  return response.data;
}

export async function verifyResult(
  resultId: string,
  request: VerifyResultRequest
): Promise<{ status: string; verification_status: string }> {
  const response = await apiClient.post(
    `/api/v1/review/results/${resultId}/verify`,
    request
  );
  return response.data;
}

export async function correctResult(
  resultId: string,
  request: CorrectResultRequest
): Promise<{ status: string; verification_status: string }> {
  const response = await apiClient.post(
    `/api/v1/review/results/${resultId}/correct`,
    request
  );
  return response.data;
}
