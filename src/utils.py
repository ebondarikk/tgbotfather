import json
from collections import namedtuple
from functools import wraps
from typing import Any

from telebot import TeleBot, types

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


def edit_or_resend(bot: TeleBot, message: types.Message, text: str, markup: Any = None):
    try:
        return bot.edit_message_text(
            text,
            message.chat.id,
            message_id=message.id,
            reply_markup=markup
        )
    except Exception:
        msg = bot.send_message(
            message.chat.id,
            text,
            reply_markup=markup
        )
        if message.from_user.id == bot.user.id:
            bot.delete_message(message.chat.id, message_id=message.id)
        return msg
