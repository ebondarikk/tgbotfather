from telebot.async_telebot import AsyncTeleBot, types

from src.handlers.commands import start, cancel, payment

COMMANDS = {
    '/start': start,
    '/help': start,
    '/cancel': cancel,
    '/payment': payment,
}


async def command_router(bot: AsyncTeleBot, message: types.Message):
    if message.text in COMMANDS:
        return await COMMANDS[message.text](bot=bot, message=message)