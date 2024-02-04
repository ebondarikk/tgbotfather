from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.markups.bots import back_menu_option
from src.utils import bot_action, general_action, gettext as _


def start_markup() -> InlineKeyboardMarkup:
    menu = [
        [InlineKeyboardButton('🤖 ' + _('My Bots'), callback_data=bot_action('list'))],
        [InlineKeyboardButton('ℹ️ ' + _('Instructions'), callback_data=general_action('instructions'))],
        [InlineKeyboardButton('🛟 ' + _('Help'), callback_data=general_action('help'))]
    ]
    markup = InlineKeyboardMarkup(menu)
    return markup


def instructions_markup(user_id: int, instructions_enabled: bool) -> InlineKeyboardMarkup:
    action_name = '🔕 ' + _('Disable') if instructions_enabled else '🔔 ' + _('Enable')
    menu = [
        [
            InlineKeyboardButton(
            action_name,
            callback_data=general_action('instruction_switch', enable=int(not instructions_enabled))
            ),
        ],
        back_menu_option('command/start')
    ]

    markup = InlineKeyboardMarkup(menu)
    return markup
