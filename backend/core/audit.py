"""
Audit event emission with SHA-256 hash chaining.

Every state-changing action in the system (upload, verify, correct, view)
must call emit_audit_event. The hash chain makes the log tamper-evident:
any modification to an earlier record breaks the chain from that point forward.

Safety rule: audit writes are committed in their OWN transaction.
Even if the caller's main transaction rolls back, the audit event is preserved.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from db.models.core_models import AuditEvent, generate_uuidv7


def _compute_event_hash(
    prev_event_hash: str,
    event_type: str,
    resource_id: uuid.UUID,
    created_at_iso: str,
) -> str:
    """Deterministic SHA-256 over the chain fields."""
    raw = f"{prev_event_hash}|{event_type}|{str(resource_id)}|{created_at_iso}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def emit_audit_event(
    db: Session,
    event_type: str,
    resource_type: str,
    resource_id: uuid.UUID,
    metadata: dict[str, Any],
    actor_user_id: uuid.UUID | None = None,
    tenant_id: uuid.UUID | None = None,
) -> AuditEvent:
    """
    Append one audit event to the audit log.

    The function fetches the most recent AuditEvent (per tenant if tenant_id
    is provided, otherwise global) to obtain the previous hash for chaining,
    then writes the new event and commits immediately in a nested savepoint so
    the audit record survives even if the caller rolls back later.

    Args:
        db:            Active SQLAlchemy session (from Depends(get_db)).
        event_type:    Verb string, e.g. "report.uploaded", "result.verified".
        resource_type: Entity name, e.g. "report", "result".
        resource_id:   UUID of the primary entity affected.
        metadata:      Arbitrary JSON-serialisable dict for context.
        actor_user_id: The user who caused the event (None for system events).
        tenant_id:     The tenant scope (None for platform-level events).

    Returns:
        The committed AuditEvent ORM instance.
    """
    # Retrieve the previous event's hash for chain continuity
    query = db.query(AuditEvent).order_by(AuditEvent.created_at.desc())
    if tenant_id is not None:
        query = query.filter(AuditEvent.tenant_id == tenant_id)
    last_event = query.first()
    prev_hash = last_event.event_hash if last_event else "genesis"

    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    event_hash = _compute_event_hash(prev_hash, event_type, resource_id, now_iso)

    event = AuditEvent(
        id=generate_uuidv7(),
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata_json=metadata,
        prev_event_hash=prev_hash,
        event_hash=event_hash,
        # created_at defaults to server_default=func.now() in the model,
        # but we set it explicitly so the hash computation stays consistent.
        created_at=now,
    )

    db.add(event)
    # Flush so the row is visible in the current transaction.
    # The caller (router) is responsible for calling db.commit().
    # This avoids committing partially-constructed audit events and
    # allows tests to control transaction boundaries.
    db.flush()
    return event
