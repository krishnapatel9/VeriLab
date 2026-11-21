import { apiClient as api } from "./client";

export interface ConsultationTypeRule {
  id: string;
  tenant_id: string;
  name: string;
  description?: string;
  version: number;
  status: "draft" | "published" | "archived";
  approved_test_names: string[];
  suggested_test_names: string[];
  created_at: string;
  updated_at: string;
}

export interface RuleCreatePayload {
  name: string;
  description?: string;
  approved_test_names: string[];
  suggested_test_names: string[];
}

export interface RulePublishPayload {
  approved_test_names: string[];
  suggested_test_names: string[];
}

export async function fetchRules(): Promise<ConsultationTypeRule[]> {
  return api.get("/api/v1/rules");
}

export async function createRule(payload: RuleCreatePayload): Promise<ConsultationTypeRule> {
  return api.post("/api/v1/rules", payload);
}

export async function publishRule(ruleId: string, payload: RulePublishPayload): Promise<ConsultationTypeRule> {
  return api.post(`/api/v1/rules/${ruleId}/publish`, payload);
}
