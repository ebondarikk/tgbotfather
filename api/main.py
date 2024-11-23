import asyncio
import io
import traceback
import uuid

from wand.image import Image

from fastapi import FastAPI, HTTPException, Response, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from api.schemas.positions import PositionPayload, PositionFreezePayload
from settings import bucket, BOT
from src.utils import check_password, create_positions, restore_message, gettext as _, freeze_positions

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить все источники (можно указать список доменов)
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все методы (GET, POST, OPTIONS и т.д.)
    allow_headers=["*"],  # Разрешить все заголовки
)


@app.get("/")
async def root():
    return {"message": "Hello, World!"}


@app.post("/positions")
async def create_positions_from_web_app(payload: PositionPayload):
    # if not check_password(payload.bot_id, payload.password):
    #     raise HTTPException(status_code=403, detail="Invalid password")

    try:
        message = restore_message(payload.user_id, payload.message_id)

        await create_positions(BOT, payload.bot_id, payload.user_id, message, payload.data)
    except Exception as e:
        traceback.print_exc()
        await BOT.send_message(payload.user_id, _('Something went wrong. Please try again later.'))

    return Response(status_code=201)


@app.post("/upload/{user_id}")
async def upload_file(user_id: int, file: UploadFile = File(...)):
    try:
        with Image(file=io.BytesIO(await file.read())) as img:
            img.transform(resize='800x800>')  # Устанавливаем максимальные размеры

            img.format = 'jpeg'

            compressed_photo = img.make_blob('jpeg')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")

    bucket_path = f'{user_id}/{str(uuid.uuid4())}'

    blob = bucket.blob(bucket_path)
    blob.upload_from_string(compressed_photo, content_type="image/jpeg")

    return {"path": bucket_path}


@app.post("/positions/freeze")
async def freeze_positions_post(payload: PositionFreezePayload):
    asyncio.create_task(freeze_positions(BOT, payload.bot_id, payload.user_id, payload.data))

    return Response(status_code=200)

