import datetime
import json
import urllib.parse
import gettext as gtext
from functools import wraps
from typing import Any

from dateutil.relativedelta import relativedelta
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


def general_action(action_name, **kwargs):
    action_name = f'general/{action_name}'
    return action(action_name, **kwargs)


def position_action(action_name, **kwargs):
    action_name = f'position/{action_name}'
    return action(action_name, **kwargs)


def statistic_action(action_name, full_route=False, **kwargs):
    action_name = f'statistic/{action_name}' if not full_route else action_name
    return action(action_name, **kwargs)


def mail_action(action_name, **kwargs):
    action_name = f'mail/{action_name}'
    return action(action_name, **kwargs)


def get_hashed_data(call):
    return redis.hgetall(call.data) or {}


def with_db(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, db=db, **kwargs)
    return wrapper


def with_statistic_period():
    from src.markups.statistic import statistic_period_markup
    def inner(func):
        @wraps(func)
        @with_callback_data
        async def wrapper(bot, call, *args, data, **kwargs):
            if 'period' not in data:
                return await edit_or_resend(
                    bot, call.message,
                    gettext('Выберите период для аналитики {action}.').format(action=data["action_title"]),
                    statistic_period_markup(data['bot_id'], data['bot_username'], action=data['action'])
                )
            return await func(
                bot, call, data, *args, markup=statistic_period_markup(
                    data['bot_id'], data['bot_username'], action=data['action']
                ), **kwargs
            )
        return wrapper
    return inner


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
            reply_markup=markup,
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


def get_default_schedule():
    return {
        'monday': [{'from': '00:00', 'to': '23:59'}],
        'tuesday': [{'from': '00:00', 'to': '23:59'}],
        'wednesday': [{'from': '00:00', 'to': '23:59'}],
        'thursday': [{'from': '00:00', 'to': '23:59'}],
        'friday': [{'from': '00:00', 'to': '23:59'}],
        'saturday': [{'from': '00:00', 'to': '23:59'}],
        'sunday': [{'from': '00:00', 'to': '23:59'}]
    }


def get_default_welcome_text():
    return gettext('Welcome to our store. Click the "Open menu" button to make an order.')


def get_periods(period: str):
    from src.enums import StatisticPeriodEnum

    today = datetime.datetime.now()
    start_period = today
    middle_period = None
    end_period = None
    delta_days = None
    delta_months = None

    period = StatisticPeriodEnum(period)

    match period:
        case StatisticPeriodEnum.day:
            start_period = today
            middle_period = datetime.datetime(year=today.year, month=today.month, day=today.day)
            end_period = middle_period - relativedelta(days=1)
        case StatisticPeriodEnum.three_days:
            start_period = today
            middle_day = today - relativedelta(days=3)
            middle_period = datetime.datetime(year=middle_day.year, month=middle_day.month, day=middle_day.day)
            end_period = middle_period - relativedelta(days=3)
        case StatisticPeriodEnum.week:
            middle_day = today - relativedelta(days=today.weekday())
            middle_period = datetime.datetime(year=middle_day.year, month=middle_day.month, day=middle_day.day)
            end_period = middle_period - relativedelta(days=7)
        case StatisticPeriodEnum.two_weeks:
            middle_day = today - relativedelta(days=today.weekday()) - relativedelta(days=7)
            middle_period = datetime.datetime(year=middle_day.year, month=middle_day.month, day=middle_day.day)
            end_period = middle_period - relativedelta(days=14)
        case StatisticPeriodEnum.month:
            middle_period = datetime.datetime(year=today.year, month=today.month, day=1)
            end_period = middle_period - relativedelta(month=1)
        case StatisticPeriodEnum.two_months:
            middle_period = datetime.datetime(year=today.year, month=today.month, day=1) - relativedelta(months=1)
            end_period = middle_period - relativedelta(month=2)
        case StatisticPeriodEnum.three_months:
            middle_period = datetime.datetime(year=today.year, month=today.month, day=1) - relativedelta(months=2)
            end_period = middle_period - relativedelta(month=3)
        case StatisticPeriodEnum.half_year:
            middle_period = datetime.datetime(year=today.year, month=today.month, day=1) - relativedelta(months=6)
            end_period = middle_period - relativedelta(month=6)
        case StatisticPeriodEnum.year:
            middle_period = datetime.datetime(year=today.year, month=today.month, day=1) - relativedelta(months=12)
            end_period = middle_period - relativedelta(month=12)

    start_stamp = start_period.timestamp()
    middle_stamp = middle_period.timestamp()
    end_stamp = end_period.timestamp()

    return int(start_stamp), int(middle_stamp), int(end_stamp)


def get_period_orders(period, orders):
    start_period, middle_period, end_period = get_periods(period)

    first_period_orders = []
    second_period_orders = []

    for key, value in orders.items():
        value_type = type(value)
        if value_type not in (list, dict):
            continue
        if value_type == list:
            first_period_orders += [
                s['totalCost'] for s in value
                if s and start_period >= s['created_at'] > middle_period
            ]
            second_period_orders += [
                s['totalCost'] for s in value
                if s and middle_period >= s['created_at'] > end_period
            ]
        if value_type == dict:
            first_period_orders += [
                s['totalCost'] for s in value.values()
                if s and start_period >= s['created_at'] > middle_period
            ]
            second_period_orders += [
                s['totalCost'] for s in value.values()
                if s and middle_period >= s['created_at'] > end_period
            ]
    return first_period_orders, second_period_orders


def get_conversion(orders, users):
    ordered_users = []
    for key, value in orders.items():
        value_type = type(value)
        if value_type not in (list, dict):
            continue
        if value_type == list:
            ordered_users += [s['username'] for s in value if s and 'username' in s]
        if value_type == dict:
            ordered_users += [s['username'] for s in value.values() if s and 'username' in s]

    ordered_users = set(ordered_users)

    all_users = len(users) or 1

    return (len(ordered_users) / all_users) * 100
