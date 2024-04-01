import numpy
from typing import Any, Iterable

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.utils import action, position_action, subitem_action, gettext as _


def back_menu_option(back_to, **kwargs):
    return [InlineKeyboardButton('↩️ ' + _('Back'), callback_data=action(back_to, **kwargs))]


def positions_list_markup(bot_id: Any, bot_username, positions: dict, page=0, page_size=20) -> InlineKeyboardMarkup:
    if page:
        page = int(page)
    if page_size:
        page_size = int(page_size)

    position_btns = [
        InlineKeyboardButton(
            f'{index + 1}.{" 🛑 " if position_data.get("frozen") else ""} {position_data["name"]}',
            callback_data=position_action('manage', bot_id=bot_id, position_key=position_key)
        )
        for index, (position_key, position_data) in list(enumerate(positions.items()))[page*page_size:(page+1)*page_size]
    ]

    has_previous = page > 0
    has_next = len(positions) > (page + 1) * page_size

    columns = max(len(position_btns), 2)
    positions_array = numpy.array_split(
        position_btns,
        columns // 2
    )

    menu = [
        [InlineKeyboardButton('➕' + _('Create a new position'), callback_data=position_action(
            'pre_create', bot_id=bot_id))
         ],
        *[list(btns) for btns in positions_array],
    ]
    if has_previous and has_next:
        menu += [
            [
                InlineKeyboardButton(
                    '⬅️ ' + _('Previous'),
                    callback_data=position_action('list', bot_id=bot_id, page=page - 1, page_size=page_size)
                ),
                InlineKeyboardButton(
                    _('Next') + ' ➡️',
                    callback_data=position_action('list', bot_id=bot_id, page=page + 1, page_size=page_size)
                ),
            ]
        ]
    elif has_previous:
        menu += [[
            InlineKeyboardButton(
                '⬅️ ' + _('Previous'),
                callback_data=position_action('list', bot_id=bot_id, page=page - 1, page_size=page_size)
            )
        ]]
    elif has_next:
        menu += [[
            InlineKeyboardButton(
                _('Next') + ' ➡️',
                callback_data=position_action('list', bot_id=bot_id, page=page + 1, page_size=page_size)
            )
        ]]

    menu += [back_menu_option('bot/manage', bot_id=bot_id, username=bot_username)]
    markup = InlineKeyboardMarkup(menu)
    return markup


def subitem_list_markup(bot_id: Any, position_key, subitems: dict) -> InlineKeyboardMarkup:
    subitem_btns = [
        InlineKeyboardButton(
            f'{index + 1}.{" 🛑 " if subitem_data.get("frozen") else ""} {subitem_data["name"]}',
            callback_data=subitem_action('manage', bot_id=bot_id, position_key=position_key, subitem_key=subitem_key)
        )
        for index, (subitem_key, subitem_data) in enumerate(subitems.items())
    ]

    columns = max(len(subitem_btns), 2)
    subitems_array = numpy.array_split(
        subitem_btns,
        columns // 2
    )

    menu = [
        [InlineKeyboardButton('➕' + _('Create a new sub item'), callback_data=subitem_action(
            'create', bot_id=bot_id, position_key=position_key))
         ],
        *[list(btns) for btns in subitems_array],
        back_menu_option('position/manage', bot_id=bot_id, position_key=position_key)
    ]
    markup = InlineKeyboardMarkup(menu)
    return markup


def positions_create_markup(bot_id: Any):
    menu = [
        [
            InlineKeyboardButton(
                _('Simple good'), callback_data=position_action('create', bot_id=bot_id)
            ),
            InlineKeyboardButton(
                _('Grouped good'), callback_data=position_action('create', bot_id=bot_id, grouped=1)
            ),
        ],
        back_menu_option('position/list', bot_id=bot_id)
    ]
    markup = InlineKeyboardMarkup(menu)
    return markup


def subitem_manage_markup(
        bot_id: Any, position_key: str, subitem: dict, subitem_key: str, keys_to_edit: Iterable
) -> InlineKeyboardMarkup:
    menu = [
        *[[
            InlineKeyboardButton(
                '✏️' + _('{index}. Edit {key}').format(index=index+1, key=key[1]),
                callback_data=subitem_action(
                    'edit',
                    bot_id=bot_id,
                    position_key=position_key,
                    subitem_key=subitem_key,
                    edit_action=key[0]
                )
            )] for index, key in enumerate(keys_to_edit)],
        [
            InlineKeyboardButton(
                _('Defrost') if subitem.get('frozen') else '🛑 ' + _('Freeze'),
                callback_data=subitem_action(
                    'freeze',
                    bot_id=bot_id,
                    position_key=position_key,
                    subitem_key=subitem_key,
                    frozen=int(subitem.get('frozen', False))
                )
            ),
        ],
        [
            InlineKeyboardButton(
            '🗑 ' + _('Remove sub item'),
            callback_data=subitem_action(
                'delete',
                bot_id=bot_id,
                position_key=position_key,
                subitem_key=subitem_key
            ))
        ],
        back_menu_option('subitem/list', bot_id=bot_id, position_key=position_key)
    ]
    markup = InlineKeyboardMarkup(menu)
    return markup


def position_manage_markup(
        bot_id: Any, position_key: str, position: dict, keys_to_edit: Iterable, inner_callbacks: Iterable
) -> InlineKeyboardMarkup:
    menu = [
        *[[
            InlineKeyboardButton(
                '✏️' + _('{index}. Edit {key}').format(index=index+1, key=key[1]),
                callback_data=position_action(
                    'edit',
                    bot_id=bot_id,
                    position_key=position_key,
                    edit_action=key[0]
                )
            )] for index, key in enumerate(keys_to_edit)],
        *[[
            InlineKeyboardButton(
                callback[0],
                callback_data=callback[1]
            )] for callback in inner_callbacks],
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
