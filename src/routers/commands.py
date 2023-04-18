from telebot import TeleBot, types

from src.handlers.commands import start

COMMANDS = {
    '/start': start,
    '/help': start
}


def command_router(bot: TeleBot, message: types.Message):
    if message.text in COMMANDS:
        return COMMANDS[message.text](bot=bot, message=message)