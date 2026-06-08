from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import Header, HTTPException

from app.config import settings


@dataclass(frozen=True)
class AuthenticatedUser:
    id: str
    email: str | None = None


class SupabaseAuthConfigError(Exception):
    pass


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="請先登入")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="登入憑證格式不正確")

    return token.strip()


def verify_supabase_token(token: str) -> AuthenticatedUser | None:
    if not settings.supabase_url or not settings.supabase_publishable_key:
        raise SupabaseAuthConfigError("Supabase Auth 尚未設定")

    auth_url = settings.supabase_url.rstrip("/") + "/auth/v1/user"
    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": settings.supabase_publishable_key,
    }

    try:
        response = httpx.get(auth_url, headers=headers, timeout=6.0)
    except httpx.HTTPError as exc:
        raise SupabaseAuthConfigError("無法連線到 Supabase Auth") from exc

    if response.status_code in {401, 403}:
        return None
    if response.status_code >= 400:
        raise SupabaseAuthConfigError("Supabase Auth 驗證失敗")

    payload: dict[str, Any] = response.json()
    user_id = payload.get("id")
    if not isinstance(user_id, str) or not user_id:
        return None

    email = payload.get("email")
    return AuthenticatedUser(
        id=user_id,
        email=email if isinstance(email, str) else None,
    )


def get_current_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> AuthenticatedUser:
    token = _extract_bearer_token(authorization)

    try:
        user = verify_supabase_token(token)
    except SupabaseAuthConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if user is None:
        raise HTTPException(status_code=401, detail="登入憑證無效或已過期")

    return user
