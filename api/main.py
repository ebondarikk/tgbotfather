import io
import traceback
import uuid

from PIL import Image
from pillow_heif import register_heif_opener

from fastapi import FastAPI, HTTPException, Response, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from api.schemas.positions import PositionPayload
from settings import bucket, BOT
from src.utils import check_password, create_positions, restore_message, gettext as _

app = FastAPI()
register_heif_opener()

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
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG and PNG are allowed.")

    try:
        image = Image.open(io.BytesIO(await file.read()))
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid image file")

    max_size = (800, 800)
    image.thumbnail(max_size)

    original_format = image.format

    if original_format == "JPEG" and image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    byte_arr = io.BytesIO()
    image.save(byte_arr, format=original_format)
    compressed_photo = byte_arr.getvalue()

    file_extension = file.filename.split('.')[-1]
    bucket_path = f'{user_id}/{str(uuid.uuid4())}'

    blob = bucket.blob(bucket_path)
    blob.upload_from_string(compressed_photo, content_type="image/jpeg")

    return {"path": bucket_path}

