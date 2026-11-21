-- PostgreSQL 16 Row-Level Security (RLS) Policies for VeriLab
-- Ensures strict database-level multi-tenant isolation.
-- Set application tenant context prior to queries:
-- SET LOCAL app.current_tenant_id = '00000000-0000-4000-8000-000000000001';

-- Enable RLS on all tenant-scoped tables
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE results ENABLE ROW LEVEL SECURITY;
ALTER TABLE result_corrections ENABLE ROW LEVEL SECURITY;
ALTER TABLE review_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;

-- 1. Reports Policy
CREATE POLICY tenant_reports_isolation_policy ON reports
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- 2. Results Policy
CREATE POLICY tenant_results_isolation_policy ON results
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- 3. Result Corrections Policy
CREATE POLICY tenant_corrections_isolation_policy ON result_corrections
    FOR ALL
    USING (
        result_id IN (
            SELECT id FROM results WHERE tenant_id = current_setting('app.current_tenant_id')::uuid
        )
    );

-- 4. Review Items Policy
CREATE POLICY tenant_review_items_isolation_policy ON review_items
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- 5. Patients Policy
CREATE POLICY tenant_patients_isolation_policy ON patients
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- 6. Audit Events Policy
CREATE POLICY tenant_audit_events_isolation_policy ON audit_events
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);
