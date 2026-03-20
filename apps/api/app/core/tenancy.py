"""Tenant isolation policy documentation.

This module is NOT a middleware layer — it documents the tenant isolation rules
enforced by convention throughout the codebase. No new runtime behavior is added here.

RBAC and tenant isolation is enforced via FastAPI Depends() injection:
  - app.domains.auth.dependencies.require_authenticated_actor
  - Per-domain _require_<role>() helper functions

Rules
-----
ORG_ID_SOURCE_RULE
    The `org_id` for all org-scoped queries MUST come from `actor.org_id` (the
    authenticated token). It MUST NOT be accepted from the request body or query
    params for access-control decisions. Client-supplied org_id may appear in
    request bodies only when creating cross-org admin resources, and must still
    be authorized against actor.org_id.

CROSS_TENANT_RESPONSE_RULE
    When a resource exists but belongs to a different org, return 404 (not 403).
    Leaking the existence of cross-tenant resources is a data disclosure risk.

DOMAIN_BOUNDARY_RULE
    Domains MUST NOT import from each other. The only allowed cross-domain import
    is `from app.domains.auth.dependencies import require_authenticated_actor`.
    This prevents tight coupling and unintended data leakage across domains.

QUERY_FILTER_RULE
    All repository queries on org-scoped tables MUST include an org_id filter
    derived from actor.org_id. This is a defense-in-depth measure: even if an
    endpoint accidentally passes the wrong resource ID, the DB query will not
    return cross-tenant data.

ROLE_GUARD_RULE
    Every protected router endpoint MUST call a _require_<role>() guard function
    immediately after receiving the ActorContext from require_authenticated_actor.
    The guard raises HTTP 403 if the actor's role is insufficient.
"""

# Role constants — single source of truth for role strings used in guards
ROLE_ADMIN = "admin"
ROLE_PRINCIPAL = "principal"
ROLE_TEACHER = "teacher"
ROLE_PARENT = "parent"
ROLE_STUDENT = "student"

# Org-scoped query sentinel — use in comments to mark org_id filter points
ORG_SCOPED = "org_id"
