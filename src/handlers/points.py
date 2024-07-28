import re
import uuid

from telebot import types
from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery

from src.markups.managers import manager_list_markup
from src.markups.points import point_list_markup
from src.states import PointStates
from src.utils import with_db, gettext as _, edit_or_resend, with_callback_data, send_message_with_cancel_markup, \
    step_handler, point_action


@with_db
async def get_point_list(
        bot, bot_id, user_id, message: types.Message, text, db, **kwargs
):
    bot_data = db.child(f'bots/{user_id}/{bot_id}').get()
    points = db.child(f'points/{bot_id}').get() or {}

    text_to_send = text or _('Select a pick-up point to manage or add a new one')

    markup = point_list_markup(bot_id, bot_username=bot_data['username'], points=points)

    await edit_or_resend(bot, message, text_to_send, markup)


@with_callback_data
async def point_list(bot: AsyncTeleBot, call: CallbackQuery, data, message: str = None):
    bot_id = data.get('bot_id')
    return await get_point_list(bot, bot_id, call.from_user.id, call.message, message)


@with_callback_data
@with_db
async def point_create(bot: AsyncTeleBot, call: CallbackQuery, data, db):
    bot_id = data.get('bot_id')
    username = data.get('bot_username')
    user_id = data.get('user_id')
    managers = db.child(f'managers/{bot_id}').get()
    manager_key = data.get('manager_key')

    create_data = {
        'bot_id': bot_id,
        'bot_username': username,
        'edit': False
    }

    await bot.set_state(call.from_user.id, PointStates.create, call.message.chat.id)

    if len(managers) > 1 and not manager_key:
        managers_markup = manager_list_markup(
            bot_id, user_id, username, managers, action=point_action, action_name='create', create=False
        )

        await edit_or_resend(
            bot,
            call.message,
            _('Firstly, choose a manager for new pick-up point.'),
            markup=managers_markup,
            parse_mode="HTML"
        )
    else:
        await bot.set_state(call.from_user.id, PointStates.create, call.message.chat.id)
        create_data['manager_key'] = manager_key or managers.keys()[0]

        async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data.update(**create_data)

        await send_message_with_cancel_markup(
            bot,
            call.message.chat.id,
            _('Send me a name of a pick-up point.')
        )

    return


@with_callback_data
@with_db
async def point_create_choose_manager(bot: AsyncTeleBot, call: CallbackQuery, data, db):
    bot_id = data.get('bot_id')
    username = data.get('username')
    manager_key = data.get('manager_key')

    create_data = {
        'bot_id': bot_id,
        'bot_username': username,
        'edit': False,
        'manager_key': manager_key
    }

    await bot.set_state(call.from_user.id, PointStates.create, call.message.chat.id)

    async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        data.update(**create_data)

    await send_message_with_cancel_markup(
        bot,
        call.message.chat.id,
        _('Send me a name of a pick-up point.')
    )


@step_handler
@with_db
async def point_create_step(message, bot: AsyncTeleBot, db):
    if message.content_type != 'text':
        return

    name = message.text

    if len(name) < 5:
        return await bot.send_message(message.chat.id, _('Oops. Too short name.'))

    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        bot_id = data['bot_id']
        data['name'] = name
        data['id'] = str(uuid.uuid4())
        await point_save(bot, message, data)

    msg_text = _('Pick-up point was added successfully. What\'s next?')

    return await get_point_list(bot, bot_id, message.from_user.id, message, msg_text)


@with_db
@with_callback_data
async def manager_manage(bot: AsyncTeleBot, call: CallbackQuery, db, data):
    bot_id = data.get('bot_id')
    bot_username = data.get('bot_username')
    manager_key = data.get('manager_key')
    manager_data = db.child(f'managers/{bot_id}/{manager_key}').get()

    markup = manager_manage_markup(bot_id, bot_username, manager_key, manager_data)

    text = _(
        "This is manager @{username}"
    ).format(username=manager_data.get('username'))

    if manager_data.get('is_admin'):
        text += '\n' + '👑 ' + _('Admin')
    if manager_data.get('is_active'):
        text += '\n' + '✅ ' + _('Active')

    text += '\n' + _('Select action.')

    return await edit_or_resend(
        bot,
        call.message,
        text=text,
        markup=markup
    )


@with_callback_data
@with_db
async def manager_activate(bot: AsyncTeleBot, call: CallbackQuery, db, data):
    bot_id = data.get('bot_id')
    manager_key = data.get('manager_key')
    manager_username = None

    managers = db.child(f'managers/{bot_id}').get()
    for manager_id, manager_data in managers.items():
        if manager_id == manager_key:
            manager_username = manager_data['username']
            db.child(f'managers/{bot_id}/{manager_id}').update({'is_active': True})
        elif manager_data.get('is_active'):
            db.child(f'managers/{bot_id}/{manager_id}').update({'is_active': False})

    return await get_manager_list(
        bot,
        bot_id,
        call.from_user.id,
        call.message,
        _('Now @{username} accept orders. What\'s next?').format(username=manager_username)
    )


@with_callback_data
@with_db
async def manager_delete(bot: AsyncTeleBot, call: CallbackQuery, db, data):
    bot_id = data.get('bot_id')
    manager_key = data.get('manager_key')

    manager_data = db.child(f'managers/{bot_id}/{manager_key}').get()
    manager_username = manager_data.get('username')

    if manager_data.get('is_admin'):
        return await bot.send_message(
            call.message.chat.id,
            _('Oops. Admin cannot be removed.')
        )
    if manager_data.get('is_active'):
        return await bot.send_message(
            call.message.chat.id,
            _('Oops. Active manager cannot be removed.')
        )

    db.child(f'managers/{bot_id}/{manager_key}').delete()

    return await get_manager_list(
        bot,
        bot_id,
        call.from_user.id,
        call.message,
        _('Manager @{username} was deleted. What\'s next?').format(username=manager_username)
    )


@with_db
async def point_save(bot: AsyncTeleBot, message: types.Message, data: dict, db):
    edit = data.pop('edit', False)
    bot_id = data.pop('bot_id')
    data.pop('bot_username', None)
    point_id = data.get('id')

    await bot.delete_state(message.from_user.id, message.chat.id)

    if edit:
        path = data.pop('path')
        db.child(path).update(data)
    else:
        db.child(f'points/{bot_id}/{point_id}').update(data)

    return True
