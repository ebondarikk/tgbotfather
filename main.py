import asyncio
import traceback

import telebot
from telebot.types import ShippingOption, LabeledPrice

import settings
from telebot.async_telebot import AsyncTeleBot
from telebot import asyncio_filters
from telebot.asyncio_storage import StateRedisStorage
from settings import REDIS_HOST, REDIS_PORT
from src.routers.callbacks import callback_router
from src.routers.commands import command_router
from src.routers.steps import steps_router
from src.routers.web_app import web_app_router

storage = StateRedisStorage(REDIS_HOST, REDIS_PORT)
bot = AsyncTeleBot(settings.BOT_TOKEN, state_storage=storage)
bot.add_custom_filter(asyncio_filters.StateFilter(bot))


def check_callback(call):
    return True


@bot.callback_query_handler(func=check_callback)
async def callback_handler(call):
    print('callback')
    return await callback_router(bot, call)


@bot.message_handler(func=lambda msg: msg.text.startswith('/'))
async def command_handler(message):
    print('command')
    return await command_router(bot, message)


@bot.message_handler(state='*', content_types=['photo', 'document', 'text'])
async def step_handler(message):
    print('step')
    return await steps_router(bot, message)


@bot.message_handler(content_types='web_app_data')
async def web_app_handler(message):
    print('web app')
    return await web_app_router(bot, message)


@bot.shipping_query_handler(func=lambda query: True)
async def shipping(shipping_query):
    print(shipping_query)
    await bot.answer_shipping_query(shipping_query.id, ok=True, shipping_options=settings.shipping_options,
                                    error_message='Oh, seems like our Dog couriers are having a lunch right now. Try again later!')


asyncio.run(
    bot.set_my_commands(
        [
            telebot.types.BotCommand("/start", "Запуск бота"),
            telebot.types.BotCommand("/help", "Помощь"),
        ]
    )
)


class ExceptionHandler:
    def handle(self):
        try:
            raise self
        except Exception:
            traceback.print_exc()


async def main():
    try:
        bot.exception_handler = ExceptionHandler
        await bot.infinity_polling()
    except Exception:
        raise

asyncio.run(main())
