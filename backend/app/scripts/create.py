from app.core.db import Base, async_engine, async_session_factory
from app.infra.theory.models import TheoryBD, TheoryBlockBD

async def create_all():
        async with async_engine.begin() as conn:
            async_engine.echo = False
            print(Base.metadata.tables.keys())
            await conn.run_sync(Base.metadata.drop_all) #TODO убрать в проде
            await conn.run_sync(Base.metadata.create_all)
            print('tables created')
            async_engine.echo = True