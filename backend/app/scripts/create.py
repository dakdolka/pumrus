from app.core.db import Base, async_engine, async_session_factory
from app.infra.theory.models import TheoryBD, TheoryBlockBD
import asyncio

async def create_all():
        async with async_engine.begin() as conn:
            async_engine.echo = False
            await conn.run_sync(Base.metadata.create_all)
            async_engine.echo = True

if __name__ == "__main__":
    asyncio.run(create_all())