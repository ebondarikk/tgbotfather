from typing import Any

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.utils import point_action, action, gettext as _


def back_menu_option(back_to, **kwargs):
    return [InlineKeyboardButton('↩️ ' + _('Back'), callback_data=action(back_to, **kwargs))]


def point_list_markup(bot_id: Any, bot_username, points: dict) -> InlineKeyboardMarkup:
    point_btns = [
        InlineKeyboardButton(
            f'{index + 1}. {point_data["name"]}',
            callback_data=point_action('manage', bot_id=bot_id, point_key=point_key)
        )
        for index, (point_key, point_data) in enumerate(points.items())
    ]

    menu = [
        [InlineKeyboardButton(
            '➕' + _('Add pick-up point'),
            callback_data=point_action('create', bot_id=bot_id, username=bot_username))
        ],
        *[[mngr] for mngr in point_btns],
        back_menu_option('bot/manage', bot_id=bot_id, username=bot_username)
    ]

    markup = InlineKeyboardMarkup(menu)
    return markup