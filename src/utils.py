import json
from functools import wraps
from typing import Any

from telebot.async_telebot import AsyncTeleBot, types
from telebot.types import KeyboardButton

from settings import redis, db, bucket


def action(action_name, **kwargs):
    data = {"action": action_name, **kwargs}
    key = hex(hash(json.dumps(data)))
    redis.hset(key, mapping=data)
    return key


def bot_action(action_name, **kwargs):
    action_name = f'bot/{action_name}'
    return action(action_name, **kwargs)


def position_action(action_name, **kwargs):
    action_name = f'position/{action_name}'
    return action(action_name, **kwargs)


def get_hashed_data(call):
    return redis.hgetall(call.data) or {}


def with_db(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, db=db, **kwargs)
    return wrapper


def step_handler(func):
    @wraps(func)
    def wrapper(message: types.Message, *args, bot: AsyncTeleBot, **kwargs):
        if message.text == '/cancel':
            from src.handlers.commands import cancel
            cancel(bot=bot, message=message)
        return func(bot=bot, message=message, *args, **kwargs)
    return wrapper


async def send_message_with_cancel_markup(bot: AsyncTeleBot, *args, **kwargs):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton('/cancel'))
    return await bot.send_message(*args, **kwargs, reply_markup=markup)


def with_callback_data(func):
    @wraps(func)
    def wrapper(call, *args, **kwargs):
        data = get_hashed_data(call)
        return func(*args, call=call, data=data, **kwargs)
    return wrapper


def with_bucket(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, bucket=bucket, **kwargs)
    return wrapper


async def edit_or_resend(bot: AsyncTeleBot, message: types.Message, text: str, markup: Any = None):
    try:
        return await bot.edit_message_text(
            text,
            message.chat.id,
            message_id=message.id,
            reply_markup=markup
        )
    except Exception:
        msg = await bot.send_message(
            message.chat.id,
            text,
            reply_markup=markup
        )
        if message.from_user.id == bot.user.id:
            await bot.delete_message(message.chat.id, message_id=message.id)
        return msg
