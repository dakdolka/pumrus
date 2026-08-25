from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware

from app.core.db import async_session_factory
from app.infra.system.models import AdminAuditLogBD


logger = logging.getLogger(__name__)


class AdminAuditMiddleware(BaseHTTPMiddleware):
    """Records every owner-side mutation without persisting secrets or bodies."""

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if (
            request.method in {"POST", "PUT", "PATCH", "DELETE"}
            and "/v2/admin" in request.url.path
        ):
            try:
                async with async_session_factory() as db:
                    db.add(AdminAuditLogBD(
                        method=request.method,
                        path=request.url.path[:512],
                        status_code=response.status_code,
                        remote_address=(request.client.host[:96] if request.client else None),
                        user_agent=(request.headers.get("user-agent") or "")[:1000],
                        details={},
                    ))
                    await db.commit()
            except Exception:
                # An unavailable audit sink must never turn a successful content
                # publication into a failed HTTP response.
                logger.exception("Could not persist an admin audit event")
        return response
