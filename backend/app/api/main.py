from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.tasks.general.router import router as task_router
from app.api.tasks.sessions.router import router as task_session_router
from app.api.theory.router import router as theory_router
from app.api.user.general.router import router as users_router
from app.api.user.mistakes.router import router as user_mistakes_router
from app.api.v2.router import router as v2_router
from app.core.db import async_engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with async_engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
    yield
    await async_engine.dispose()


app = FastAPI(lifespan=lifespan, root_path="/api")


@app.get("/healthz", tags=["system"])
async def healthcheck():
    return {"status": "ok", "database": "postgresql"}


app.include_router(theory_router)
app.include_router(task_router)
app.include_router(task_session_router)
app.include_router(user_mistakes_router)
app.include_router(users_router)
app.include_router(v2_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
