from typing import Any

import numpy
from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from src.utils import with_callback_data, mail_action, gettext as _, action


def back_menu_option(back_to, **kwargs):
    return [InlineKeyboardButton('⬅️ ' + _('Back'), callback_data=action(back_to, **kwargs))]


def mail_list_markup(bot_id: Any, bot_username, mails: dict) -> InlineKeyboardMarkup:
    mail_btns = []
    for index, (mail_key, mail_data) in enumerate(mails.items()):

        if content := mail_data.get("content"):
            if len(content) > 10:
                name = content[:10] + '...'
            else:
                name = content
        else:
            name = 'No text'

        # if images := mail_data.get("images"):
        #     name += f' ({len(images)} images)'

        name = ('🔊 ' if mail_data['published'] else '🔇 ') + name

        mail_btns.append(
            InlineKeyboardButton(
                f'{index + 1}. {name}',
                callback_data=mail_action('manage', bot_id=bot_id, mail_key=mail_key),
            )
        )

    columns = max(len(mail_btns), 2)
    mails_array = numpy.array_split(
        mail_btns,
        columns // 2
    )

    menu = [
        [InlineKeyboardButton('➕ ' + _('Create a new Mail'), callback_data=mail_action('create', bot_id=bot_id))],
        *[list(btns) for btns in mails_array],
        back_menu_option('bot/manage', bot_id=bot_id, username=bot_username)
    ]
    markup = InlineKeyboardMarkup(menu)
    return markup


def mail_manage_markup(bot_id: Any, mail_key: str, mailing: dict) -> InlineKeyboardMarkup:
    menu = [
        [InlineKeyboardButton(
            '🔊 ' + _('Publish'),
            callback_data=mail_action(
                'publish',
                bot_id=bot_id,
                mail_key=mail_key,
            ))],
        back_menu_option('mail/list', bot_id=bot_id)
    ]
    markup = InlineKeyboardMarkup(menu)
    return markup
