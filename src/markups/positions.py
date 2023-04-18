from typing import Any

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.utils import action, position_action


def back_menu_option(back_to, **kwargs):
    return [InlineKeyboardButton('<< Back', callback_data=action(back_to, **kwargs))]


def positions_list_markup(bot_id: Any, positions: dict) -> InlineKeyboardMarkup:
    menu = [
        [InlineKeyboardButton('Create a new position', callback_data=position_action('create', bot_id=bot_id))],
        *[
            [InlineKeyboardButton(
                f'{index + 1}. {position_data["name"]}',
                callback_data=position_action('manage', bot_id=bot_id, position_key=position_key)
            )
                for index, (position_key, position_data) in enumerate(positions.items())]
        ],
        back_menu_option('bot/manage', bot_id=bot_id)
    ]
    markup = InlineKeyboardMarkup(menu)
    return markup


def position_manage_markup(bot_id: Any, position_key: str, position: dict) -> InlineKeyboardMarkup:
    menu = [
        *[[
            InlineKeyboardButton(
                f'{index + 1}. Edit {key}',
                callback_data=position_action(
                    'edit',
                    bot_id=bot_id,
                    position_key=position_key,
                    edit_action=key
                )
            )] for index, key in enumerate(position.keys())],
        [InlineKeyboardButton(
            'Remove position',
            callback_data=position_action(
                'delete',
                bot_id=bot_id,
                position_key=position_key,
            ))],
        back_menu_option('position/list', bot_id=bot_id)
    ]
    markup = InlineKeyboardMarkup(menu)
    return markup
