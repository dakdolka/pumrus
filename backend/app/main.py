import json
from pprint import pprint
from fastapi import Body, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
import asyncmy
from contextlib import asynccontextmanager
# from data import Orm
from fastapi.middleware.cors import CORSMiddleware
# from data import Year
# from app.models import Photo, Points, User_info, Person, Info
# from config import settings
# from data import settings
# from app.bot import send_to_moderation, bot, dp
from pydantic import BaseModel
# async def save_images(image: Photo):
#     # image_base64 = base64.b64encode(image).decode("utf-8")
#     # image.img_del = resp.json().data.delete_url
from crud.create import create_all


class MyException(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     while True:
#         try:
#             conn = await asyncmy.connect(
#                 host=settings.host,
#                 user=settings.user,
#                 password=settings.password,
#                 database=settings.db,
#                 port=int(settings.port)
#             )
#             await conn.ensure_closed()
#             print("MySQL is ready!")
#             break
#         except Exception as e:
#             print("Waiting for MySQL to be ready...", str(e))
#             await asyncio.sleep(1)
#     await Orm.create_all()
#     asyncio.create_task(dp.start_polling(bot))
#     yield


app = FastAPI(root_path='/api')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешает все домены, можно указать список доменов, например: ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],  # Разрешены все методы HTTP
    allow_headers=["*"],  # Разрешены все заголовки
)


@app.get('/ping')
async def ping():
    return JSONResponse(status_code=200, content="pong")


asyncio.run(create_all())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
