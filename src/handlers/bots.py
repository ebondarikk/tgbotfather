import telebot
from telebot import types, TeleBot
from telebot.types import KeyboardButton

from src.handlers.commands import start
from src.utils import with_db, with_callback_data, edit_or_resend
from src.markups.bots import bots_list_markup, bot_manage_markup


def bot_create(bot: TeleBot, call: types.CallbackQuery):
    cancel_btn = KeyboardButton('cancel')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(cancel_btn)
    msg = edit_or_resend(
        bot,
        call.message,
        'Create a new bot via BotFather and send me a token',
        markup
    )
    bot.register_next_step_handler(msg, create_bot_step, bot=bot)


@with_db
def bot_list(bot: TeleBot, call: types.CallbackQuery, db):
    username = call.from_user.username
    bots = db.child('bots').child(username).get() or {}
    markup = bots_list_markup(bots)
    bot.edit_message_text('Select TeBot to manage', call.message.chat.id, message_id=call.message.id, reply_markup=markup)


@with_callback_data
def bot_manage(bot: TeleBot, call: types.CallbackQuery, data: dict):
    markup = bot_manage_markup(data['bot_id'])
    bot.edit_message_text('Select Action', call.message.chat.id, message_id=call.message.id, reply_markup=markup)


@with_db
@with_callback_data
def bot_delete(bot: TeleBot, call: types.CallbackQuery, db, data):
    bot_id = data.get('bot_id')
    username = call.from_user.username
    db.child(f'bots/{username}/{bot_id}').delete()
    bot.send_message(call.message.chat.id, 'Success')


@with_db
def create_bot_step(message: types.Message, bot: TeleBot, db):
    token = message.text
    if token == 'cancel':
        start(bot=bot, message=message, edit=True)
        return
    newbot = TeleBot(token)
    try:
        username = newbot.user.username
        fullname = newbot.user.full_name
        bot_id = newbot.user.id
    except telebot.apihelper.ApiException:
        msg = bot.send_message(message.from_user.id, 'Invalid bot token')
        bot.register_next_step_handler(msg, create_bot_step, bot=bot)
    else:
        db.child('bots').child(message.from_user.username).child(str(bot_id)).update(
            {'username': username, 'fullname': fullname, 'token': token}
        )
        success_msg = f'Tebot {fullname} was created successfully'
        start(bot=bot, message=message, msg_text=success_msg, edit=True)