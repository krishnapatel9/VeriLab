from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid

from api.dependencies import get_db, require_role
from db.models.core_models import ConsultationTypeRule, User, generate_uuidv7
from schemas.rules import RuleItemSchema, RuleCreateRequest, RulePublishRequest
from core.audit import emit_audit_event

router = APIRouter(prefix="/api/v1/rules", tags=["Rules"])


@router.get("", response_model=List[RuleItemSchema])
def list_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "doctor", "reviewer", "uploader"]))
):
    """List all consultation type rules for the active tenant."""
    rules = (
        db.query(ConsultationTypeRule)
        .filter(ConsultationTypeRule.tenant_id == current_user.tenant_id)
        .order_by(ConsultationTypeRule.updated_at.desc())
        .all()
    )
    return rules


@router.post("", response_model=RuleItemSchema)
def create_rule(
    request: RuleCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Clinical Admin: Create a new consultation type rule."""
    rule = ConsultationTypeRule(
        id=generate_uuidv7(),
        tenant_id=current_user.tenant_id,
        name=request.name,
        description=request.description,
        version=1,
        status="published",
        approved_test_names=request.approved_test_names,
        suggested_test_names=request.suggested_test_names,
        created_by_user_id=current_user.id,
    )
    db.add(rule)

    emit_audit_event(
        db=db,
        event_type="rule.created",
        resource_type="consultation_type_rule",
        resource_id=rule.id,
        metadata={"name": rule.name, "version": rule.version, "test_count": len(rule.approved_test_names)},
        actor_user_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )
    db.commit()
    db.refresh(rule)
    return rule


@router.post("/{rule_id}/publish", response_model=RuleItemSchema)
def publish_rule_version(
    rule_id: uuid.UUID,
    request: RulePublishRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Clinical Admin: Publish an updated version of an existing consultation type rule."""
    existing = (
        db.query(ConsultationTypeRule)
        .filter(ConsultationTypeRule.id == rule_id, ConsultationTypeRule.tenant_id == current_user.tenant_id)
        .first()
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Consultation type rule not found")

    new_version = existing.version + 1
    existing.status = "archived"

    new_rule = ConsultationTypeRule(
        id=generate_uuidv7(),
        tenant_id=current_user.tenant_id,
        name=existing.name,
        description=existing.description,
        version=new_version,
        status="published",
        approved_test_names=request.approved_test_names,
        suggested_test_names=request.suggested_test_names,
        created_by_user_id=current_user.id,
    )
    db.add(new_rule)

    emit_audit_event(
        db=db,
        event_type="rule.published",
        resource_type="consultation_type_rule",
        resource_id=new_rule.id,
        metadata={
            "name": new_rule.name,
            "prev_version": existing.version,
            "new_version": new_rule.version,
            "test_count": len(new_rule.approved_test_names),
        },
        actor_user_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )
    db.commit()
    db.refresh(new_rule)
    return new_rule
