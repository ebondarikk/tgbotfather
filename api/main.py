import traceback

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from telebot.async_telebot import AsyncTeleBot

from api.schemas.positions import PositionPayload
from settings import db, bucket, BOT
from src.utils import check_password, create_positions, restore_message, gettext as _

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
