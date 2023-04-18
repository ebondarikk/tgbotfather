from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.utils import bot_action


def start_markup() -> InlineKeyboardMarkup:
    menu = [
        [InlineKeyboardButton('My Bots', callback_data=bot_action('list'))]
    ]
    markup = InlineKeyboardMarkup(menu)
    return markup
