from __future__ import annotations

from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_token
from app.domains.auth.repository import InMemoryAuthRepository

_security = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class ActorContext:
    user_id: str
    role: str
    org_id: str


async def require_authenticated_actor(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security),
) -> ActorContext:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        payload = decode_token(credentials.credentials)
    except (jwt.InvalidTokenError, ValueError, TypeError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required") from exc

    user_id = str(payload.get("sub", ""))
    role = str(payload.get("role", ""))
    org_id = str(payload.get("org_id", ""))
    if not user_id or not role or not org_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    actor = InMemoryAuthRepository().get_by_user_id(user_id)
    if actor is None or actor.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if actor.role != role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if actor.org_id != org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    return ActorContext(user_id=actor.user_id, role=actor.role, org_id=actor.org_id)
