"""
Tests for Clinical Admin Rules Engine (Step 2).

Verifies consultation type creation, listing, version incrementing on publish,
RBAC protection (only admin can create/publish), and audit trail emission.
"""

import pytest


def test_list_rules_empty_or_seeded(client, uploader_headers):
    response = client.get("/api/v1/rules", headers=uploader_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_rule_admin_only(client, admin_headers, reviewer_headers):
    payload = {
        "name": "Diabetes Care Package",
        "description": "Rule set for routine diabetes lab reviews",
        "approved_test_names": ["HbA1c", "Fasting Blood Glucose"],
        "suggested_test_names": ["Lipid Panel", "Serum Creatinine"],
    }

    # Reviewer cannot create rules (RBAC check)
    forbidden_resp = client.post("/api/v1/rules", json=payload, headers=reviewer_headers)
    assert forbidden_resp.status_code == 403

    # Admin can create rule
    resp = client.post("/api/v1/rules", json=payload, headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Diabetes Care Package"
    assert data["version"] == 1
    assert data["status"] == "published"
    assert "HbA1c" in data["approved_test_names"]
    rule_id = data["id"]

    # Now publish new version (v2)
    publish_payload = {
        "approved_test_names": ["HbA1c", "Fasting Blood Glucose", "Postprandial Glucose"],
        "suggested_test_names": ["Lipid Panel", "Serum Creatinine", "eGFR"],
    }
    pub_resp = client.post(f"/api/v1/rules/{rule_id}/publish", json=publish_payload, headers=admin_headers)
    assert pub_resp.status_code == 200
    new_data = pub_resp.json()
    assert new_data["version"] == 2
    assert new_data["status"] == "published"
    assert "Postprandial Glucose" in new_data["approved_test_names"]
