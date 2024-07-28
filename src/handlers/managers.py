import re

from telebot import types
from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery

from src.markups.managers import manager_list_markup, manager_manage_markup
from src.states import ManagerStates
from src.utils import with_db, gettext as _, edit_or_resend, with_callback_data, send_message_with_cancel_markup, \
    step_handler


@with_db
async def get_manager_list(
        bot, bot_id, user_id, message: types.Message, text, db, **kwargs
):
    bot_data = db.child(f'bots/{user_id}/{bot_id}').get()
    managers = db.child(f'managers/{bot_id}').get() or {}

    text_to_send = text or _('Select a manager to manage or add a new one')

    markup = manager_list_markup(bot_id, user_id=user_id, bot_username=bot_data['username'], managers=managers)

    await edit_or_resend(bot, message, text_to_send, markup)


@with_callback_data
async def manager_list(bot: AsyncTeleBot, call: CallbackQuery, data, message: str = None):
    bot_id = data.get('bot_id')
    return await get_manager_list(bot, bot_id, call.from_user.id, call.message, message)


@with_callback_data
async def manager_create(bot: AsyncTeleBot, call: CallbackQuery, data):
    bot_id = data.get('bot_id')
    user_id = data.get('user_id')
    username = data.get('username')

    await bot.set_state(call.from_user.id, ManagerStates.create, call.message.chat.id)

    async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        data['bot_id'] = bot_id
        data['user_id'] = user_id
        data['bot_username'] = username
        data['edit'] = False

    await send_message_with_cancel_markup(
        bot,
        call.message.chat.id,
        _('Send me a username (@my_manager) or link (t.me/my_manager) of person to add.\n'
          '<b>Important: The person must be user of your bot</b> @{bot_username}'
          ).format(bot_username=username),
        parse_mode="HTML"
    )


@step_handler
@with_db
async def manager_create_step(message, bot: AsyncTeleBot, db):
    if message.content_type != 'text':
        return

    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        bot_id = data['bot_id']
        bot_username = data.pop('bot_username')

    name = message.text.strip()
    usename_pattern = '^@\w{4,}$'
    link_username_pattern = '^(https:\/\/)?t.me\/\w{4,}$'

    if re.findall(usename_pattern, name):
        username = name.replace('@', '')
    elif re.findall(link_username_pattern, name):
        username = name.split('/')[-1]
    else:
        return await bot.send_message(message.chat.id, _('Oops. Invalid username format.'))

    users = db.child(f'users/{bot_id}').get()

    try:
        manager_id, manager_data = next(
            (u_id, u_data) for u_id, u_data in users.items() if u_data.get('username') == username
        )
    except StopIteration:
        return await bot.send_message(
            message.chat.id,
            _('Oops. Could not find this user in users of your bot. '
              'Ask him to run the bot @{bot_username} and try again.').format(
                bot_username=bot_username
            )
        )

    if manager_data.get('is_bot'):
        return await bot.send_message(
            message.chat.id,
            _('Oops. Seems like it is a bot. Bot can not be a manager.')
        )

    exists_managers = db.child(f'managers/{bot_id}').get() or {}

    if manager_id in exists_managers:
        return await bot.send_message(message.chat.id, _('Oops. This user is already manager.'))

    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['id'] = manager_id
        data.update(**manager_data)
        data['is_admin'] = False
        data['is_active'] = False
        data['edit'] = False
        await manager_save(bot, message, data)

    # if 'edit':
    #     msg_text = _('Category was updated successfully. What\'s next?')
    # else:
    msg_text = _('Manager was added successfully. Now @{username} can accept orders. What\'s next?').format(
        username=manager_data['username']
    )

    return await get_manager_list(bot, bot_id, message.from_user.id, message, msg_text)


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
async def manager_save(bot: AsyncTeleBot, message: types.Message, data: dict, db):
    edit = data.pop('edit', False)
    bot_id = data.pop('bot_id')
    data.pop('bot_username', None)
    manager_id = data.get('id')

    await bot.delete_state(message.from_user.id, message.chat.id)

    if edit:
        path = data.pop('path')
        db.child(path).update(data)
    else:
        db.child(f'managers/{bot_id}/{manager_id}').update(data)

    return True
