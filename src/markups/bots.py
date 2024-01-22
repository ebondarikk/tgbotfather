import datetime
from typing import Any

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.utils import action, bot_action, position_action, gettext as _, statistic_action, mail_action, category_action


def back_menu_option(back_to, **kwargs):
    return [InlineKeyboardButton('⬅️ ' + _('Back'), callback_data=action(back_to, **kwargs))]


def is_need_update(bot_data):
    return (
            bot_data.get('last_updates')
            and
            bot_data.get('last_deploy', datetime.datetime.min)
            < datetime.datetime.fromisoformat(bot_data['last_updates'])
    )


def bots_list_markup(bots: dict) -> InlineKeyboardMarkup:
    menu = [
        [InlineKeyboardButton('➕' + _('Create new TeBot'), callback_data=bot_action('create'))],
        *[
            [InlineKeyboardButton(f'{index + 1}. {bot_data["fullname"]} {"✅" if bot_data.get("paid") else ""}',
                                  callback_data=bot_action('manage', bot_id=bot_id, username=bot_data['username']))
             for index, (bot_id, bot_data) in enumerate(bots.items())]
        ],
        back_menu_option('command/start')
    ]
    markup = InlineKeyboardMarkup(menu)
    return markup


def bot_manage_markup(bot_id: Any, bot_username: any = None) -> InlineKeyboardMarkup:
    menu = [
        [InlineKeyboardButton('🛒 ' + _('Positions'), callback_data=position_action('list', bot_id=bot_id))],
        [InlineKeyboardButton('🏷 ' + _('Categories'), callback_data=category_action('list', bot_id=bot_id))],
        [InlineKeyboardButton('📣 ' + _('Mailings'), callback_data=mail_action('list', bot_id=bot_id))],
        [InlineKeyboardButton(
            '📈 ' + _('Statistic'),
            callback_data=statistic_action('list', bot_id=bot_id, bot_username=bot_username)
        )],
        [InlineKeyboardButton('👋 ' + _('Welcome message'), callback_data=bot_action('welcome_text', bot_id=bot_id))],
        [InlineKeyboardButton('💱 ' + _('Currency'), callback_data=bot_action('currency', bot_id=bot_id))],
        [InlineKeyboardButton('📆 ' + _('Schedule'), callback_data=bot_action('schedule', bot_id=bot_id))],
        [InlineKeyboardButton('🛠 ' + _('Deploy'), callback_data=bot_action('deploy', bot_id=bot_id))],
        [InlineKeyboardButton('🗑 ' + _('Remove TeBot'), callback_data=bot_action('delete', bot_id=bot_id))],
        back_menu_option('bot/list')
    ]
    markup = InlineKeyboardMarkup(menu)
    return markup


def bot_currency_markup(bot_id: Any, bot_username: str, text='', with_cancel=True) -> InlineKeyboardMarkup:
    menu = [
        [InlineKeyboardButton('🇷🇺 ' + 'RUB', callback_data=bot_action('currency', text=text, currency='RUB', bot_id=bot_id))],
        [InlineKeyboardButton('🇧🇾 ' + 'BYN', callback_data=bot_action('currency', text=text, currency='BYN', bot_id=bot_id))],
    ]

    if with_cancel:
        menu.append(back_menu_option('bot/manage', bot_id=bot_id, username=bot_username))

    markup = InlineKeyboardMarkup(menu)
    return markup


def bot_welcome_text_markup(bot_id: Any, bot_username: str) -> InlineKeyboardMarkup:
    menu = [
        [InlineKeyboardButton('✏️ ' + 'Update text', callback_data=bot_action('welcome_text_update', bot_id=bot_id))],
        back_menu_option('bot/manage', bot_id=bot_id, username=bot_username)
    ]

    return InlineKeyboardMarkup(menu)