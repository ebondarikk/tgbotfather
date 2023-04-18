import settings
from telebot import TeleBot
from src.routers.callbacks import callback_router
from src.routers.commands import command_router

bot = TeleBot(settings.BOT_TOKEN)


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    return callback_router(bot, call)


@bot.message_handler(func=lambda msg: msg.text.startswith('/'))
def command_handler(message):
    return command_router(bot, message)


bot.polling(none_stop=True, interval=0)
