import json
import urllib.parse

import aiodocker
import requests
import telebot.apihelper
from telebot import TeleBot
from telebot.async_telebot import types, AsyncTeleBot

from settings import GITHUB_ACCESS
from src.exceptions import BotAlreadyExistsException
from src.utils import (
    with_db, with_callback_data, send_message_with_cancel_markup, step_handler, get_image_url,
    with_bucket, make_function_public, gettext as _, edit_or_resend, get_default_schedule, get_default_welcome_text,
    deploy_script
)
from src.markups.bots import bots_list_markup, bot_manage_markup, bot_currency_markup, bot_welcome_text_markup, \
    bot_communication_markup
from src.states import BotStates


@with_bucket
@with_db
async def bot_create(bot: AsyncTeleBot, call: types.CallbackQuery, bucket, db):
    await bot.set_state(call.from_user.id, BotStates.token, call.message.chat.id)

    is_instructions_enabled = db.child(f'botly_users/{call.from_user.id}/instructions_enabled').get()

    if is_instructions_enabled:
        await bot.send_message(
            call.message.chat.id,
            _('Uploading video-instruction. Please, wait')
        )
        await bot.send_video(
            call.message.chat.id,
            video=open('instructions/bot_create.mov', 'rb'),
            supports_streaming=True
        )
    else:
        await bot.send_message(
            call.message.chat.id,
            _('Video instruction available. To get it, go to the Instructions section and activate them.')
        )
    await send_message_with_cancel_markup(
        bot,
        call.message.chat.id,
        _('Create a new bot via @BotFather and send me a token. Use the video instructions to make it more clear')
    )


@with_db
async def get_bot_list(bot, user_id, message, text, db):
    bots = db.child('bots').child(str(user_id)).get() or {}
    markup = bots_list_markup(bots)
    return await edit_or_resend(
        bot,
        message,
        text or _('Select a bot to view and customize or Create a new one.'),
        markup
    )


async def bot_list(bot: AsyncTeleBot, call: types.CallbackQuery):
    user_id = call.from_user.id
    return await get_bot_list(
        bot,
        user_id,
        call.message,
        None
    )


@with_callback_data
async def bot_manage(bot: AsyncTeleBot, call: types.CallbackQuery, data: dict):
    markup = bot_manage_markup(data['bot_id'], data['username'])
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
    user_id = call.from_user.id
    db.child(f'bots/{user_id}/{bot_id}').delete()
    await get_bot_list(
        bot,
        call.from_user.id,
        call.message,
        _('Bot was deleted successfully. What\'s next?').format(fullname=data.get('fullname'))
    )


def web_app_keyboard(schedule, bot_id, locale="ru"):
    keyboard = types.ReplyKeyboardMarkup(row_width=1)
    schedule = urllib.parse.quote(json.dumps(schedule))
    web_app = types.WebAppInfo(
        f"https://master--chimerical-quokka-229115.netlify.app/?schedule={schedule}&locale={locale}&bot_id={bot_id}&route=schedule"
    )
    one_butt = types.KeyboardButton(text=_("Update Schedule"), web_app=web_app)
    keyboard.add(one_butt)

    return keyboard


@with_db
@with_callback_data
async def bot_schedule_get(bot: AsyncTeleBot, call: types.CallbackQuery, db, data):
    bot_id = data.get('bot_id')
    user_id = call.from_user.id

    schedule = db.child(f'bots/{user_id}/{bot_id}/schedule').get()

    message = _('That\'s schedule of your Bot. You can update it by clicking on "Update Schedule" button \n\n')

    days = {
        'monday': _('Monday'),
        'tuesday': _('Tuesday'),
        'wednesday': _('Wednesday'),
        'thursday': _('Thursday'),
        'friday': _('Friday'),
        'saturday': _('Saturday'),
        'sunday': _('Sunday'),
    }

    for weekday in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
        day_schedule = schedule.get(weekday)
        if not day_schedule:
            day_schedule_str = '_' + _('off-day') + '_'
        else:
            day_schedule_str = '_' + ', '.join(f'{s["from"]} – {s["to"]}' for s in day_schedule if s) + '_'
        message += '*' + days[weekday] + ': *' + day_schedule_str + '\n'
    return await bot.send_message(
        chat_id=call.message.chat.id,
        text=message,
        parse_mode='Markdown',
        reply_markup=web_app_keyboard(schedule, bot_id)
    )


@with_db
@with_callback_data
async def bot_welcome_text(bot: AsyncTeleBot, call: types.CallbackQuery, db, data):
    bot_id = data.get('bot_id')
    user_id = call.from_user.id
    welcome_text = db.child(f'bots/{user_id}/{bot_id}/welcome_text').get()
    msg = _('<i>This is your welcome message:</i>') + '\n\n' + welcome_text
    markup = bot_welcome_text_markup(bot_id, db.child(f'bots/{user_id}/{bot_id}/username').get())

    return await bot.send_message(call.message.chat.id, msg, parse_mode='HTML', reply_markup=markup)


@with_callback_data
async def bot_welcome_text_update(bot: AsyncTeleBot, call: types.CallbackQuery, data):
    bot_id = data.get('bot_id')

    await bot.set_state(call.from_user.id, BotStates.welcome_text, call.message.chat.id)

    async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        data['bot_id'] = bot_id

    await bot.send_message(call.message.chat.id, _('Send me a new welcome message'))


@with_callback_data
@with_db
async def bot_communication(bot: AsyncTeleBot, call: types.CallbackQuery, data, db):
    bot_id = data.get('bot_id')
    bot_username = db.child(f'bots/{call.message.chat.id}/{bot_id}/username').get()

    if data.get('is_active') is not None:
        db.child(f'bots/{call.message.chat.id}/{bot_id}/communication').set(bool(int(data['is_active'])))

    is_active = db.child(f'bots/{call.message.chat.id}/{bot_id}/communication').get()

    if is_active is None:
        is_active = True

    markup = bot_communication_markup(bot_id, bot_username, is_active)
    await edit_or_resend(
        bot,
        message=call.message,
        markup=markup,
        text=_(
            'Communication is {status}. Disable communication with managers if you want to stop receiving messages from clients'
        ).format(status=_('enabled') if is_active else _('disabled')),
    )


@step_handler
@with_db
async def bot_welcome_text_updated(bot: AsyncTeleBot, message: types.Message, db):
    new_message = message.html_text or message.text

    if not new_message:
        return await bot.send_message(message.chat.id, _('Message undefined. Try again'))

    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        bot_id = data['bot_id']

    db.child(f'bots/{message.from_user.id}/{bot_id}').update({'welcome_text': new_message})

    await bot.delete_state(message.from_user.id, message.chat.id)

    markup = bot_manage_markup(bot_id, db.child(f'bots/{message.from_user.id}/{bot_id}/username').get())

    return await edit_or_resend(
        bot,
        message,
        _('Welcome text was updated. What\'s next?'),
        markup=markup
    )



@with_db
async def bot_schedule_save(bot: AsyncTeleBot, message: types.Message, db):
    data = json.loads(message.web_app_data.data)

    try:
        bot_id = int(data['bot_id'])
        schedule = data['schedule']
    except Exception:
        return await bot.send_message(
            message.chat.id,
            'Incorrect data received',
        )

    user_id = message.from_user.id
    bot_username = db.child(f'bots/{user_id}/{bot_id}/username').get()
    db.child(f'bots/{user_id}/{bot_id}/schedule').update(schedule)

    return await bot.send_message(
        message.chat.id,
        'Расписание успешно обновлено.', #TODO: translate
        reply_markup=bot_manage_markup(bot_id, bot_username)
    )


@with_db
@with_callback_data
async def bot_currency_update(bot: AsyncTeleBot, call: types.CallbackQuery, data, db):
    bot_id = data.get('bot_id')
    user_id = call.from_user.id

    new_currency = data.get('currency')
    bot_username = db.child(f'bots/{user_id}/{bot_id}/username').get()

    if new_currency:
        db.child(f'bots/{user_id}/{bot_id}/currency').set(new_currency)
        msg = _('Currency was successfully updated to {currency}. What\'s next?').format(currency=new_currency)
        markup = bot_manage_markup(bot_id, bot_username)
    else:
        current_currency = db.child(f'bots/{user_id}/{bot_id}/currency').get()
        msg = _('Your current currency is {currency}. Please, choose a new currency').format(currency=current_currency)
        markup = bot_currency_markup(bot_id, bot_username)

    return await edit_or_resend(
        bot,
        call.message,
        msg,
        markup=markup
    )


@with_db
@with_callback_data
@with_bucket
async def bot_deploy2(bot: AsyncTeleBot, call: types.CallbackQuery, db, data, bucket):
    bot_id = data.get('bot_id')
    user_id = call.from_user.id
    positions = db.child(f'bots/{user_id}/{bot_id}/positions').get()
    paid = db.child(f'bots/{user_id}/{bot_id}/paid').get()

    if not positions:
        return await bot.send_message(
            call.message.chat.id,
            _('The bot doesn\'t have any position yet. Create positions, then launch deploy')
        )

    docker = aiodocker.Docker()
    bot_data = db.child(f'bots/{user_id}/{bot_id}').get()
    function_name = bot_data['username']
    msg = _('Success. Try your bot @{bot_username}').format(bot_username=bot_data["username"])

    await bot.send_message(call.message.chat.id, _('Start building your bot. Please, wait...'))
    print('...building...')
    try:
        result = await docker.images.build(
            remote=f'https://{GITHUB_ACCESS}@github.com/chillingturtle/tg-bot.git',
            nocache=True,
            tag='bot_image',
            buildargs={
                'FIREBASE_PROJECT': 'telegram-bot-1-c1cfe',
                'FIREBASE_TOKEN': '1//0cbja13u4muayCgYIARAAGAwSNwF-L9IrYdBKdOTcj-1kLNF3tBwbQceG_Rx4laIPFYh8v325IzrVLv81H6k9Me7pXht5blvdvZk',
                'TG_TOKEN': bot_data['token'],
                'TG_OWNER_CHAT_ID': str(call.message.chat.id),
                'TG_BOT_NAME': function_name,
                'TG_BOT_ID': str(bot_id),
                'TG_BOT_OWNER_USERNAME': user_id
            }
        )
    except Exception as e:
        print('exception')
        print(e)
        msg = _('Ooops. Something went wrong ({error})')
        return await bot.send_message(call.message.chat.id, msg)
    else:
        if 'error' in result[-1]:
            print('error when building')
            msg = _('Ooops. Something went wrong ({error})').format(error=str(result[-1]['error']))
            print(str(result[-1]['error']))
        else:
            make_function_public(function_name)
            function_path = f'https://us-central1-telegram-bot-1-c1cfe.cloudfunctions.net/{function_name}'
            resp = requests.get(f'https://api.telegram.org/bot{bot_data["token"]}/setWebhook?url={function_path}')
            if not resp.ok:
                msg = _('Ooops. Something went wrong ({error})').format(error=resp.text)
                print(resp.text)
    finally:
        delete_result = await docker.images.delete(name='bot_image', force=True)
        print(delete_result)

    await bot.send_message(call.message.chat.id, msg)


async def set_webhook(bot_id, user_id, token):

    url = f'https://botly-shop-oqwwiafbbq-uc.a.run.app/{user_id}/{bot_id}/webhook'
    resp = requests.get(f'https://api.telegram.org/bot{token}/setWebhook?url={url}')
    return resp.ok


@with_db
@with_callback_data
@with_bucket
async def bot_deploy(bot: AsyncTeleBot, call: types.CallbackQuery, db, data, bucket):
    bot_id = data.get('bot_id')
    user_id = call.from_user.id

    url = f'https://botly-shop-oqwwiafbbq-uc.a.run.app/{user_id}/{bot_id}/webhook'
    bot_data = db.child(f'bots/{user_id}/{bot_id}').get()
    # msg = 'success'
    resp = requests.get(f'https://api.telegram.org/bot{bot_data["token"]}/setWebhook?url={url}')
    if not resp.ok:
        msg = _('Ooops. Something went wrong ({error})').format(error=resp.text)
        print(resp.text)

        await bot.send_message(call.message.chat.id, msg)

    #TODO: end expirement
    # positions = db.child(f'bots/{user_id}/{bot_id}/positions').get()


    # if not positions:
    #     return await bot.send_message(
    #         call.message.chat.id,
    #         _('The bot doesn\'t have any position yet. Create positions, then launch deploy')
    #     )
    #
    # bot_data = db.child(f'bots/{user_id}/{bot_id}').get()
    # function_name = bot_data['username']
    # msg = _('Success. Try your bot @{bot_username}').format(bot_username=bot_data["username"])
    #
    # await bot.send_message(call.message.chat.id, _('Start deploying your bot. Please, wait...'))
    # print('...deploying...')
    #
    # try:
    #     await deploy_script(
    #         tg_token=bot_data['token'],
    #         tg_owner_chat_id=str(call.message.chat.id),
    #         tg_bot_name=function_name,
    #         tg_bot_id=str(bot_id),
    #         tg_bot_owner_user_id=user_id,
    #         firebase_project='telegram-bot-1-c1cfe',
    #         firebase_token='1//0cbja13u4muayCgYIARAAGAwSNwF-L9IrYdBKdOTcj-1kLNF3tBwbQceG_Rx4laIPFYh8v325IzrVLv81H6k9Me7pXht5blvdvZk',
    #     )
    # except Exception as e:
    #     msg = _('Ooops. Something went wrong. Try again later')
    #     print(e)
    # else:
    #     make_function_public(function_name)
    #     function_path = f'https://us-central1-telegram-bot-1-c1cfe.cloudfunctions.net/{function_name}'
    #     resp = requests.get(f'https://api.telegram.org/bot{bot_data["token"]}/setWebhook?url={function_path}')
    #     if not resp.ok:
    #         msg = _('Ooops. Something went wrong ({error})').format(error=resp.text)
    #         print(resp.text)
    #
    # await bot.send_message(call.message.chat.id, 'success')


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
            data['currency'] = 'BYN'
            data['welcome_text'] = get_default_welcome_text()
            data['paid'] = False
            data['last_updates'] = None
            data['last_deploy'] = None

        try:
            await bot_save(bot=bot, message=message)
        except BotAlreadyExistsException:
            await bot.send_message(
                message.chat.id,
                _('Bot with this token already exists. Try to input another token')
            )
        except Exception as e:
            await bot.send_message(
                message.chat.id,
                _('Ooops. {e}. Try to input another token').format(e=e)
            )
        else:
            result = await set_webhook(bot_id, message.from_user.id, token)

            if not result:
                msg = _('Не удалось установить вебхук. Пожалуйста, обратитесь в поддержку')
                await bot.send_message(message.chat.id, msg)

            await edit_or_resend(
                bot,
                message,
                _('Bot {fullname} was created successfully.').format(
                    fullname=data.get('fullname'),
                ),
                markup=bot_manage_markup(bot_id, username)
            )
            await bot.delete_state(message.from_user.id, message.chat.id)


@with_db
async def bot_save(bot: AsyncTeleBot, message: types.Message, db):
    async with bot.retrieve_data(message.from_user.id, message.chat.id) as bot_data:
        data = bot_data

    user_bots = db.child('bots').child(str(message.from_user.id)).get()
    if user_bots and data.get('bot_id') in user_bots.keys():
        raise BotAlreadyExistsException

    db.child('bots').child(str(message.from_user.id)).child(data.get('bot_id')).update(
        {
            'username': data.get('username'),
            'fullname': data.get('fullname'),
            'paid': data.get('paid'),
            'welcome_text': data.get('welcome_text'),
            'token': data.get('token'),
            'currency': data.get('currency'),
            'schedule': get_default_schedule()
        }
    )

    db.child(f'managers/{data.get("bot_id")}/{message.from_user.id}').update(
        {
            'id': message.from_user.id,
            'username': message.from_user.username,
            'first_name': message.from_user.first_name,
            'is_active': True,
            'is_admin': True
        }
    )
