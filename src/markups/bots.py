from typing import Any

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.utils import action, bot_action, position_action


def back_menu_option(back_to, **kwargs):
    return [InlineKeyboardButton('<< Back', callback_data=action(back_to, **kwargs))]


def bots_list_markup(bots: dict) -> InlineKeyboardMarkup:
    menu = [
        [InlineKeyboardButton('Create new TeBot', callback_data=bot_action('create'))],
        *[
            [InlineKeyboardButton(f'{index + 1}. {bot_data["fullname"]}',
                                  callback_data=bot_action('manage', bot_id=bot_id))
             for index, (bot_id, bot_data) in enumerate(bots.items())]
        ],
        back_menu_option('command/start')
    ]
    markup = InlineKeyboardMarkup(menu)
    return markup


def bot_manage_markup(bot_id: Any) -> InlineKeyboardMarkup:
    menu = [
        [InlineKeyboardButton('Positions', callback_data=position_action('list', bot_id=bot_id))],
        [InlineKeyboardButton('Remove TeBot', callback_data=bot_action('delete', bot_id=bot_id))],
        back_menu_option('bot/list')
    ]
    markup = InlineKeyboardMarkup(menu)
    return markup
