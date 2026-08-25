import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v2.router import router as v2_router
from app.api.v2.admin_router import router as v2_admin_router
from app.api.v2.monetization_admin_router import router as v2_monetization_admin_router
from app.api.v2.payments_router import router as v2_payments_router
from app.api.v2.internal_router import router as v2_internal_router
from app.api.v2.operations_router import (
    admin_router as v2_operations_admin_router,
    public_router as v2_operations_public_router,
)
from app.core.admin_audit import AdminAuditMiddleware
from app.core.rate_limit import RateLimitMiddleware
from app.core.config import settings
from app.core.db import async_engine
from app.core.payment_worker import payment_worker


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with async_engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
    payment_stop = asyncio.Event()
    payment_task = (
        asyncio.create_task(payment_worker(payment_stop))
        if settings.payments_enabled else None
    )
    try:
        yield
    finally:
        if payment_task:
            payment_stop.set()
            await payment_task
        await async_engine.dispose()


app = FastAPI(lifespan=lifespan, root_path="/api")


@app.get("/healthz", tags=["system"])
async def healthcheck():
    return {"status": "ok", "database": "postgresql"}


app.include_router(v2_router)
app.include_router(v2_admin_router)
app.include_router(v2_monetization_admin_router)
app.include_router(v2_payments_router)
app.include_router(v2_internal_router)
app.include_router(v2_operations_public_router)
app.include_router(v2_operations_admin_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AdminAuditMiddleware)
app.add_middleware(RateLimitMiddleware)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
