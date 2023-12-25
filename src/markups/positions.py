import numpy
from typing import Any

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.utils import action, position_action, gettext as _


def back_menu_option(back_to, **kwargs):
    return [InlineKeyboardButton('⬅️ ' + _('Back'), callback_data=action(back_to, **kwargs))]


def positions_list_markup(bot_id: Any, bot_username, positions: dict) -> InlineKeyboardMarkup:
    position_btns = [
        InlineKeyboardButton(
            f'{index + 1}. {position_data["name"]}',
            callback_data=position_action('manage', bot_id=bot_id, position_key=position_key)
        )
        for index, (position_key, position_data) in enumerate(positions.items())
    ]
    columns = max(len(position_btns), 2)
    positions_array = numpy.array_split(
        position_btns,
        columns // 2
    )

    menu = [
        [InlineKeyboardButton('➕' + _('Create a new position'), callback_data=position_action('create', bot_id=bot_id))],
        *[list(btns) for btns in positions_array],
        back_menu_option('bot/manage', bot_id=bot_id, username=bot_username)
    ]
    markup = InlineKeyboardMarkup(menu)
    return markup


def position_manage_markup(bot_id: Any, position_key: str, position: dict) -> InlineKeyboardMarkup:
    menu = [
        *[[
            InlineKeyboardButton(
                '✏️' + _('{index}. Edit {key}').format(index=index+1, key=key),
                callback_data=position_action(
                    'edit',
                    bot_id=bot_id,
                    position_key=position_key,
                    edit_action=key
                )
            )] for index, key in enumerate(position.keys())],
        [InlineKeyboardButton(
            '🗑 ' + _('Remove position'),
            callback_data=position_action(
                'delete',
                bot_id=bot_id,
                position_key=position_key,
            ))],
        back_menu_option('position/list', bot_id=bot_id)
    ]
    markup = InlineKeyboardMarkup(menu)
    return markup
