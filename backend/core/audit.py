"""
Audit event emission with SHA-256 hash chaining.

Every state-changing action in the system (upload, verify, correct, view)
must call emit_audit_event. The hash chain makes the log tamper-evident:
any modification to an earlier record breaks the chain from that point forward.

Safety rule: emit_audit_event() flushes but does not commit. Call it BEFORE the
caller's db.commit() so the state change and its audit record land in the same
transaction — a change can never be committed without its audit event (or vice
versa). verify_chain() re-computes the whole chain to detect tampering.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from db.models.core_models import AuditEvent, generate_uuidv7


def _ts(dt: datetime) -> str:
    """Canonical UTC timestamp — SQLite drops tzinfo, so hash the naive UTC form."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")


def _compute_event_hash(
    prev_event_hash: str,
    event_type: str,
    resource_type: str,
    resource_id: uuid.UUID,
    actor_user_id: uuid.UUID | None,
    tenant_id: uuid.UUID | None,
    metadata: dict[str, Any],
    created_at: datetime,
) -> str:
    """Deterministic SHA-256 over every field of the event, so editing any of them breaks the chain."""
    raw = json.dumps(
        [prev_event_hash, event_type, resource_type, str(resource_id),
         str(actor_user_id), str(tenant_id), metadata, _ts(created_at)],
        sort_keys=True, default=str, separators=(",", ":"),
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _chain_query(db: Session, tenant_id: uuid.UUID | None):
    q = db.query(AuditEvent)
    q = q.filter(AuditEvent.tenant_id == tenant_id) if tenant_id is not None         else q.filter(AuditEvent.tenant_id.is_(None))
    return q


def verify_chain(db: Session, tenant_id: uuid.UUID | None) -> bool:
    """True if every event's prev-hash links up and its stored hash re-computes."""
    prev = "genesis"
    for e in _chain_query(db, tenant_id).order_by(AuditEvent.created_at.asc(), AuditEvent.id.asc()):
        expected = _compute_event_hash(
            prev, e.event_type, e.resource_type, e.resource_id,
            e.actor_user_id, e.tenant_id, e.metadata_json, e.created_at,
        )
        if e.prev_event_hash != prev or e.event_hash != expected:
            return False
        prev = e.event_hash
    return True


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

    The function fetches the most recent AuditEvent in the tenant's chain
    (tenant_id=None is its own platform chain) to obtain the previous hash,
    then adds the new event and flushes. The caller commits.

    Args:
        db:            Active SQLAlchemy session (from Depends(get_db)).
        event_type:    Verb string, e.g. "report.uploaded", "result.verified".
        resource_type: Entity name, e.g. "report", "result".
        resource_id:   UUID of the primary entity affected.
        metadata:      Arbitrary JSON-serialisable dict for context.
        actor_user_id: The user who caused the event (None for system events).
        tenant_id:     The tenant scope (None for platform-level events).

    Returns:
        The flushed AuditEvent ORM instance.
    """
    # Retrieve the previous event's hash for chain continuity
    # ponytail: no row lock, so two simultaneous writers can fork a tenant's chain;
    # add a per-tenant sequence / SELECT FOR UPDATE on Postgres.
    last_event = (
        _chain_query(db, tenant_id)
        .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
        .first()
    )
    prev_hash = last_event.event_hash if last_event else "genesis"

    now = datetime.now(timezone.utc)
    event_hash = _compute_event_hash(
        prev_hash, event_type, resource_type, resource_id,
        actor_user_id, tenant_id, metadata, now,
    )

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
