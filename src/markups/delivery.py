from typing import Any

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.utils import delivery_action, gettext as _, action

def back_menu_option(back_to, **kwargs):
    return [InlineKeyboardButton('↩️ ' + _('Back'), callback_data=action(back_to, **kwargs))]


def delivery_manage_markup(bot_id: Any, bot_username, delivery_data: dict) -> InlineKeyboardMarkup:
    menu = [
        [InlineKeyboardButton(
            '✅ ' + _('Activate delivery') if not delivery_data['is_active'] else '❌ ' + _('Deactivate delivery'),
            callback_data=delivery_action(
                'activate',
                bot_id=bot_id,
            ))],
        [InlineKeyboardButton(
            '💵 ' + _('Cost of delivery'),
            callback_data=delivery_action(
                'cost',
                bot_id=bot_id,
                activate=int(not delivery_data['is_active'])
            ))],
        [InlineKeyboardButton(
            '📃 ' + _('Minimum check'),
            callback_data=delivery_action(
                'min_check',
                bot_id=bot_id,
                activate=int(not delivery_data['is_active'])
            ))],
        [InlineKeyboardButton(
            '⚙️ ' + _('Delivery condition'),
            callback_data=delivery_action(
                'condition',
                bot_id=bot_id,
                activate=int(not delivery_data['is_active'])
            ))],
        back_menu_option('bot/manage', bot_id=bot_id, username=bot_username)
    ]
    markup = InlineKeyboardMarkup(menu)
    return markup


def delivery_condition_manage_markup(bot_id: Any, delivery_conditions, selected_condition) -> InlineKeyboardMarkup:
    menu = [
        *[[
            InlineKeyboardButton(
                f'{"✅" if selected_condition[0] == condition[0] else ""} {condition[0]}',
                callback_data=delivery_action(
                    'set_condition',
                    bot_id=bot_id,
                    selected_condition=key,
                )
            )] for key, condition in delivery_conditions.items()],
        back_menu_option('delivery/manage', bot_id=bot_id)
    ]
    markup = InlineKeyboardMarkup(menu)
    return markup