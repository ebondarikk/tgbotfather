import telebot.apihelper
from telebot import TeleBot
from telebot.async_telebot import types, AsyncTeleBot

from src.exceptions import BotAlreadyExistsException
from src.utils import with_db, with_callback_data, send_message_with_cancel_markup, step_handler
from src.markups.bots import bots_list_markup, bot_manage_markup
from src.states import BotStates


async def bot_create(bot: AsyncTeleBot, call: types.CallbackQuery):
    await bot.set_state(call.from_user.id, BotStates.token, call.message.chat.id)
    await send_message_with_cancel_markup(
        bot,
        call.message.chat.id,
        'Create a new bot via BotFather and send me a token'
    )


@with_db
async def bot_list(bot: AsyncTeleBot, call: types.CallbackQuery, db):
    username = call.from_user.username
    bots = db.child('bots').child(username).get() or {}
    markup = bots_list_markup(bots)
    await bot.edit_message_text(
        'Select TeBot to manage',
        call.message.chat.id,
        message_id=call.message.id,
        reply_markup=markup
    )


@with_callback_data
async def bot_manage(bot: AsyncTeleBot, call: types.CallbackQuery, data: dict):
    markup = bot_manage_markup(data['bot_id'])
    await bot.edit_message_text(
        f'This is @{data["username"]}. Select Action',
        call.message.chat.id,
        message_id=call.message.id,
        reply_markup=markup
    )


@with_db
@with_callback_data
async def bot_delete(bot: AsyncTeleBot, call: types.CallbackQuery, db, data):
    bot_id = data.get('bot_id')
    username = call.from_user.username
    db.child(f'bots/{username}/{bot_id}').delete()
    await bot.send_message(call.message.chat.id, 'Success')


@step_handler
async def bot_token_step(message: types.Message, bot: AsyncTeleBot):
    token = message.text
    newbot = TeleBot(token)
    try:
        username = newbot.user.username
        fullname = newbot.user.full_name
        bot_id = newbot.user.id
    except telebot.apihelper.ApiException as e:
        await bot.send_message(message.from_user.id, 'Invalid bot token. Send the token again.')
    else:
        async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['bot_id'] = str(bot_id)
            data['token'] = token
            data['username'] = username
            data['fullname'] = fullname

        try:
            await bot_save(bot=bot, message=message)
        except Exception as e:
            await bot.send_message(
                message.chat.id,
                f'Ooops. {e}. Try to input another token'
            )
        else:
            await bot.send_message(
                message.chat.id,
                f'Tebot {data.get("fullname")} was created successfully'
            )
            await bot.delete_state(message.from_user.id, message.chat.id)


@with_db
async def bot_save(bot: AsyncTeleBot, message: types.Message, db):
    async with bot.retrieve_data(message.from_user.id, message.chat.id) as bot_data:
        data = bot_data

    if data.get('bot_id') in db.child('bots').child(message.from_user.username).get().keys():
        raise BotAlreadyExistsException

    db.child('bots').child(message.from_user.username).child(data.get('bot_id')).update(
        {'username': data.get('username'), 'fullname': data.get('fullname'), 'token': data.get('token')}
    )

