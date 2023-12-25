from typing import Any

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.enums import StatisticPeriodEnum
from src.utils import action, statistic_action, gettext as _


def back_menu_option(back_to, **kwargs):
    return [InlineKeyboardButton('⬅️ ' + _('Back'), callback_data=action(back_to, **kwargs))]


def statistic_period_markup(bot_id: Any, bot_username: str, action: str) -> InlineKeyboardMarkup:
    menu = [
        [InlineKeyboardButton(
            period.value.capitalize(), callback_data=statistic_action(
                action, full_route=True, bot_id=bot_id, bot_username=bot_username, period=period.value
            )
        )]
        for period in StatisticPeriodEnum
    ] + [back_menu_option('statistic/list', bot_id=bot_id, bot_username=bot_username)]
    markup = InlineKeyboardMarkup(menu)
    return markup


def statistic_list_markup(bot_id: Any, bot_username) -> InlineKeyboardMarkup:
    menu = [
        [InlineKeyboardButton(
            '💰 ' + _('Revenue'), callback_data=statistic_action(
                'revenue', action_title=_('Revenue'), bot_id=bot_id, bot_username=bot_username
            )
        )],
        [InlineKeyboardButton(
            '🔢 ' + _('Number of orders'),
            callback_data=statistic_action(
                'orders_number', action_title=_('Number of orders'), bot_id=bot_id, bot_username=bot_username
            )
        )],
        [InlineKeyboardButton(
            '🧾 ' + _('Average bill'),
            callback_data=statistic_action(
                'avg_bill', action_title=_('Average bill'), bot_id=bot_id, bot_username=bot_username
            )
        )],
        [InlineKeyboardButton(
            '💯 ' + _('CR, Conversion'),
            callback_data=statistic_action('conversion', bot_id=bot_id, bot_username=bot_username)
        )],
        back_menu_option('bot/manage', bot_id=bot_id, username=bot_username)
    ]
    markup = InlineKeyboardMarkup(menu)
    return markup