from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.utils import bot_action, general_action, gettext as _


def start_markup() -> InlineKeyboardMarkup:
    menu = [
        [InlineKeyboardButton('🤖 ' + _('My Bots'), callback_data=bot_action('list'))],
        [InlineKeyboardButton('🛟 ' + _('Help'), callback_data=general_action('help'))]
    ]
    markup = InlineKeyboardMarkup(menu)
    return markup
