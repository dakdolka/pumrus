from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
import asyncmy
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.scripts.create import create_all
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    while True:
        try:
            conn = await asyncmy.connect(
                host=settings.host,
                user=settings.user,
                password=settings.password,
                database=settings.db,
                port=int(settings.port)
            )
            await conn.ensure_closed()
            print("MySQL is ready!")
            break
        except Exception as e:
            print("Waiting for MySQL to be ready...", str(e))
            break
    await create_all()
    yield


app = FastAPI(lifespan=lifespan, root_path='/api')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешает все домены, можно указать список доменов, например: ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],  # Разрешены все методы HTTP
    allow_headers=["*"],  # Разрешены все заголовки
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
