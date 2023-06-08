import json
import urllib.parse

import docker
import requests
import telebot.apihelper
from telebot import TeleBot
from telebot.async_telebot import types, AsyncTeleBot

from src.exceptions import BotAlreadyExistsException
from src.utils import with_db, with_callback_data, send_message_with_cancel_markup, step_handler, get_image_url, \
    with_bucket, make_function_public, gettext as _
from src.markups.bots import bots_list_markup, bot_manage_markup
from src.states import BotStates


async def bot_create(bot: AsyncTeleBot, call: types.CallbackQuery):
    await bot.set_state(call.from_user.id, BotStates.token, call.message.chat.id)
    await send_message_with_cancel_markup(
        bot,
        call.message.chat.id,
        _('Create a new bot via @BotFather and send me a token')
    )


@with_db
async def bot_list(bot: AsyncTeleBot, call: types.CallbackQuery, db):
    username = call.from_user.username
    bots = db.child('bots').child(username).get() or {}
    markup = bots_list_markup(bots)
    await bot.edit_message_text(
        _('Select TeBot to manage'),
        call.message.chat.id,
        message_id=call.message.id,
        reply_markup=markup
    )


@with_callback_data
async def bot_manage(bot: AsyncTeleBot, call: types.CallbackQuery, data: dict):
    markup = bot_manage_markup(data['bot_id'])
    await bot.edit_message_text(
        _('This is @{bot_username}. Select Action').format(bot_username=data["username"]),
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
    await bot.send_message(call.message.chat.id, _('Success'))


@with_db
@with_callback_data
@with_bucket
async def bot_deploy(bot: AsyncTeleBot, call: types.CallbackQuery, db, data, bucket):
    bot_id = data.get('bot_id')
    username = call.from_user.username
    positions = db.child(f'bots/{username}/{bot_id}/positions').get()
    if not positions:
        return await bot.send_message(
            call.message.chat.id,
            _('The bot doesn\'t have any position yet. Create positions, then launch deploy')
        )
    positions_list = []
    for position in positions.values():
        positions_list.append(
            {
                'name': position['name'],
                'price': position['price'],
                'image': get_image_url(position['image']),
                'quantity': 0
            }
        )
    positions_json = json.dumps(positions_list)
    parsed_positions = urllib.parse.quote(positions_json)

    client = docker.DockerClient()
    bot_data = db.child(f'bots/{username}/{bot_id}').get()
    function_name = bot_data['username']
    msg = _('Success. Try your bot @{bot_username}').format(bot_username=bot_data["username"])

    await bot.send_message(call.message.chat.id, _('Start building your bot. Please, wait...'))
    try:
        print('...building...')
        client.images.build(
            path='https://ebondarikk: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@github.com/chillingturtle/tg-bot.git',
            buildargs={
                'FIREBASE_PROJECT': 'telegram-bot-1-c1cfe',
                'FIREBASE_TOKEN': '1//0cbja13u4muayCgYIARAAGAwSNwF-L9IrYdBKdOTcj-1kLNF3tBwbQceG_Rx4laIPFYh8v325IzrVLv81H6k9Me7pXht5blvdvZk',
                'TG_TOKEN': bot_data['token'],
                'TG_OWNER_CHAT_ID': str(call.message.chat.id),
                'TG_WEBAPP_URL': f'https://harmonious-duckanoo-4d4ea5.netlify.app/?items={parsed_positions}&locale=ru&curr=BYN',
                'TG_BOT_NAME': function_name,
            }
        )
        make_function_public(function_name)
    except Exception as e:
        msg = _('Ooops. Something went wrong ({error})').format(error=str(e))
    else:
        function_path = f'https://us-central1-telegram-bot-1-c1cfe.cloudfunctions.net/{function_name}'
        resp = requests.get(f'https://api.telegram.org/bot{bot_data["token"]}/setWebhook?url={function_path}')
        if not resp.ok:
            msg = _('Ooops. Something went wrong ({error})').format(error=resp.text)

    await bot.send_message(call.message.chat.id, msg)


@step_handler
async def bot_token_step(message: types.Message, bot: AsyncTeleBot):
    token = message.text
    newbot = TeleBot(token)
    try:
        username = newbot.user.username
        fullname = newbot.user.full_name
        bot_id = newbot.user.id
    except telebot.apihelper.ApiException as e:
        await bot.send_message(message.from_user.id, _('Invalid bot token. Send the token again.'))
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
                _('Ooops. {e}. Try to input another token').format(e=e)
            )
        else:
            await bot.send_message(
                message.chat.id,
                _('Tebot {fullname} was created successfully').format(fullname=data.get('fullname'))
            )
            await bot.delete_state(message.from_user.id, message.chat.id)


@with_db
async def bot_save(bot: AsyncTeleBot, message: types.Message, db):
    async with bot.retrieve_data(message.from_user.id, message.chat.id) as bot_data:
        data = bot_data

    user_bots = db.child('bots').child(message.from_user.username).get()
    if user_bots and data.get('bot_id') in user_bots.keys():
        raise BotAlreadyExistsException

    db.child('bots').child(message.from_user.username).child(data.get('bot_id')).update(
        {'username': data.get('username'), 'fullname': data.get('fullname'), 'token': data.get('token')}
    )

