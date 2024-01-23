from typing import Any

import numpy
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.utils import category_action, action, gettext as _, position_action


def back_menu_option(back_to, **kwargs):
    return [InlineKeyboardButton('⬅️ ' + _('Back'), callback_data=action(back_to, **kwargs))]


def categories_for_position_markup(
        bot_id: Any, bot_username, categories: dict, create: bool, position_key: str = None, **kwargs
) -> InlineKeyboardMarkup:
    category_btns = [
        InlineKeyboardButton(
            f'{index + 1}. {category_data["name"]}',
            callback_data=position_action(
                'create' if create else 'edit', bot_id=bot_id, category=category_data["name"], create=create,
                edit_action='category', position_key=position_key or 0, **kwargs
            )
        )
        for index, (category_key, category_data) in enumerate(categories.items())
    ]
    columns = max(len(category_btns), 2)
    categories_array = numpy.array_split(
        category_btns,
        columns // 2
    )

    menu = [
        *[list(btns) for btns in categories_array],
        [InlineKeyboardButton(
            f'{len(categories) + 1}. ' + _('Other'),
            callback_data=position_action(
                'create' if create else 'edit', bot_id=bot_id, category='', create=create,
                edit_action='category', position_key=position_key or 0, **kwargs
            )
        )],
        back_menu_option('bot/manage' if create else 'position/list', bot_id=bot_id, username=bot_username)
    ]

    markup = InlineKeyboardMarkup(menu)
    return markup


def categories_list_markup(bot_id: Any, bot_username, categories: dict) -> InlineKeyboardMarkup:
    category_btns = [
        InlineKeyboardButton(
            f'{index + 1}. {category_data["name"]}',
            callback_data=category_action('manage', bot_id=bot_id, category_key=category_key)
        )
        for index, (category_key, category_data) in enumerate(categories.items())
    ]
    columns = max(len(category_btns), 2)
    categories_array = numpy.array_split(
        category_btns,
        columns // 2
    )

    menu = [
        [InlineKeyboardButton(
            '➕' + _('Create a new category'),
            callback_data=category_action('create', bot_id=bot_id))
        ],
        *[list(btns) for btns in categories_array],
        back_menu_option('bot/manage', bot_id=bot_id, username=bot_username)
    ]

    markup = InlineKeyboardMarkup(menu)
    return markup


def category_manage_markup(bot_id: Any, category_key: str, category: dict) -> InlineKeyboardMarkup:
    menu = [
        *[[
            InlineKeyboardButton(
                '✏️' + _('{index}. Edit {key}').format(index=index+1, key=key),
                callback_data=category_action(
                    'edit',
                    bot_id=bot_id,
                    category_key=category_key,
                    edit_action=key
                )
            )] for index, key in enumerate(category.keys())],
        [InlineKeyboardButton(
            '🗑 ' + _('Remove category'),
            callback_data=category_action(
                'delete',
                bot_id=bot_id,
                category_key=category_key,
            ))],
        back_menu_option('category/list', bot_id=bot_id)
    ]
    markup = InlineKeyboardMarkup(menu)
    return markup
