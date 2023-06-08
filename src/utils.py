import json
import urllib.parse
import gettext as gtext
from functools import wraps
from typing import Any

from google.cloud import api_keys_v2
from google.cloud.functions_v1 import CloudFunctionsServiceClient
from google.iam.v1.iam_policy_pb2 import SetIamPolicyRequest
from google.iam.v1.policy_pb2 import Policy, Binding
from google.oauth2 import service_account
from telebot.async_telebot import AsyncTeleBot, types
from telebot.types import KeyboardButton

import settings
from settings import redis, db, bucket

ru = gtext.translation('base', localedir='locale', languages=['ru'])
ru.install()

gettext = ru.gettext


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


def get_image_url(image_path):
    image_path = urllib.parse.quote(image_path).replace('/', '%2F')
    return f'https://firebasestorage.googleapis.com/v0/b/telegram-bot-1-c1cfe.appspot.com/o/{image_path}?alt=media'


def create_api_key():
    cred_file = settings.FIREBASE_CERTIFICATE
    credentials = service_account.Credentials.from_service_account_file(cred_file)
    client = api_keys_v2.ApiKeysClient(credentials=credentials)
    key = api_keys_v2.Key()
    request = api_keys_v2.CreateKeyRequest()
    request.parent = f"projects/{settings.PROJECT_ID}/locations/global"
    request.key = key
    response = client.create_key(request=request).result()
    return response


def make_function_public(function_name):
    cred_file = settings.FIREBASE_CERTIFICATE
    credentials = service_account.Credentials.from_service_account_file(cred_file)

    resource = f'projects/{settings.PROJECT_ID}/locations/us-central1/functions/{function_name}'
    policy = Policy(bindings=[Binding(role="roles/cloudfunctions.invoker", members=["allUsers"])])

    client = CloudFunctionsServiceClient(credentials=credentials)
    request = SetIamPolicyRequest(resource=resource, policy=policy)
    response = client.set_iam_policy(request=request)

    return response
