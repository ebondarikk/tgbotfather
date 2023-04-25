import asyncio
import telebot

import settings
from telebot.async_telebot import AsyncTeleBot
from telebot import asyncio_filters
from telebot.asyncio_storage import StateRedisStorage
from settings import REDIS_HOST, REDIS_PORT
from src.routers.callbacks import callback_router
from src.routers.commands import command_router
from src.routers.steps import steps_router

storage = StateRedisStorage(REDIS_HOST, REDIS_PORT)
bot = AsyncTeleBot(settings.BOT_TOKEN, state_storage=storage)
bot.add_custom_filter(asyncio_filters.StateFilter(bot))


@bot.callback_query_handler(func=lambda call: True)
async def callback_handler(call):
    return await callback_router(bot, call)


@bot.message_handler(func=lambda msg: msg.text.startswith('/'))
async def command_handler(message):
    return await command_router(bot, message)


@bot.message_handler(state='*', content_types=['photo', 'document', 'text'])
async def step_handler(message):
    return await steps_router(bot, message)


# @bot.message_handler(func=lambda msg: True)
# def message_handler(message):
#     return message_router(bot, message)

asyncio.run(
    bot.set_my_commands(
        [
            telebot.types.BotCommand("/start", "Запуск бота"),
            telebot.types.BotCommand("/help", "Помощь")
        ]
    )
)
asyncio.run(bot.polling())
