from typing import Any

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.utils import manager_action, action, gettext as _


def back_menu_option(back_to, **kwargs):
    return [InlineKeyboardButton('↩️ ' + _('Back'), callback_data=action(back_to, **kwargs))]


def manager_list_markup(bot_id: Any, bot_username, managers: dict) -> InlineKeyboardMarkup:
    manager_btns = [
        InlineKeyboardButton(
            f'{index + 1}. '
            f'{"👑 " if manager_data["is_admin"] else ""}'
            f'{"✅ " if manager_data["is_active"] else ""}'
            f'{manager_data["first_name"]}'
            f' (@{manager_data["username"]})',
            callback_data=manager_action('manage', bot_id=bot_id, manager_key=manager_key)
        )
        for index, (manager_key, manager_data) in enumerate(managers.items())
    ]

    menu = [
        [InlineKeyboardButton(
            '➕' + _('Add manager'),
            callback_data=manager_action('create', bot_id=bot_id, username=bot_username))
        ],
        *[[mngr] for mngr in manager_btns],
        back_menu_option('bot/manage', bot_id=bot_id, username=bot_username)
    ]

    markup = InlineKeyboardMarkup(menu)
    return markup


def manager_manage_markup(bot_id: Any, bot_username, manager_key, manager_data) -> InlineKeyboardMarkup:
    manager_btns = []

    if not manager_data.get('is_active'):
        manager_btns.append([
            InlineKeyboardButton(
                '✅ ' + _('Activate'),
                callback_data=manager_action('activate', bot_id=bot_id, manager_key=manager_key)
            )
        ])
        if not manager_data.get('is_admin'):
            manager_btns.append([
                InlineKeyboardButton(
                    '🗑 ' + _('Remove manager'),
                    callback_data=manager_action('delete', bot_id=bot_id, manager_key=manager_key)
                )
            ])
    manager_btns.append(back_menu_option('manager/list', bot_id=bot_id))

    markup = InlineKeyboardMarkup(manager_btns)
    return markup


