from telebot import types
from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery

from src.markups.categories import categories_list_markup, category_manage_markup, categories_for_position_markup
from src.states import CategoryStates
from src.utils import with_db, edit_or_resend, gettext as _, with_callback_data, send_message_with_cancel_markup, \
    step_handler


@with_db
async def get_category_list(
        bot, bot_id, username, message: types.Message, text, db, create: any = None, position_key: str = None, **kwargs
):
    bot_data = db.child(f'bots/{username}/{bot_id}').get()
    categories = bot_data.get('categories', {})

    text_to_send = text or _('Select a category to manage or create a new one')

    if create is not None:
        markup = categories_for_position_markup(
            bot_id, bot_data.get('username'), categories, create=create, position_key=position_key, **kwargs
        )
    else:
        markup = categories_list_markup(bot_id, bot_data.get('username'), categories)

    await edit_or_resend(bot, message, text_to_send, markup)


@with_callback_data
async def category_list(bot: AsyncTeleBot, call: CallbackQuery, data, message: str = None):
    bot_id = data.get('bot_id')
    return await get_category_list(bot, bot_id, call.from_user.username, call.message, message)


@with_callback_data
async def category_create(bot: AsyncTeleBot, call: CallbackQuery, data):
    bot_id = data.get('bot_id')
    await bot.set_state(call.from_user.id, CategoryStates.create, call.message.chat.id)

    async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        data['bot_id'] = bot_id
        data['edit'] = False

    await send_message_with_cancel_markup(
        bot,
        call.message.chat.id,
        _('Send me a name of new category.')
    )


@with_db
@with_callback_data
async def category_manage(bot: AsyncTeleBot, call: CallbackQuery, db, data):
    username = call.from_user.username
    bot_id = data.get('bot_id')
    category_key = data.get('category_key')
    category = db.child(f'bots/{username}/{bot_id}/categories/{category_key}').get()
    caption = _("""*Name:* _{name}_""").format(
        name=category['name'],
    )
    markup = category_manage_markup(bot_id, category_key, category)
    await edit_or_resend(bot, call.message, caption, markup, parse_mode="Markdown")


@with_callback_data
async def category_edit(bot: AsyncTeleBot, call: CallbackQuery, data):
    username = call.from_user.username
    bot_id = data.get('bot_id')
    category_key = data.get('category_key')
    key_to_edit = data.get('edit_action')
    path = f'bots/{username}/{bot_id}/categories/{category_key}'

    state = None
    match key_to_edit:
        case 'name':
            state = CategoryStates.name

    if state:
        await bot.set_state(call.from_user.id, state, call.message.chat.id)
        async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as state_data:
            state_data['bot_id'] = bot_id
            state_data['path'] = path
            state_data['edit'] = True

    await bot.send_message(call.message.chat.id, _('Send me new {key_to_edit}').format(key_to_edit=key_to_edit))


@step_handler
async def category_create_step(message, bot):
    if message.content_type != 'text':
        return

    name = message.text

    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        edit = data.get('edit')
        bot_id = data.get('bot_id')
        data['name'] = name
        await category_save(bot, message, data)

    if edit:
        msg_text = _('Category was updated successfully. What\'s next?')
    else:
        msg_text = _('Category was created successfully. What\'s next?')

    return await get_category_list(bot, bot_id, message.from_user.username, message, msg_text)


@with_db
async def category_save(bot: AsyncTeleBot, message: types.Message, data: dict, db):
    edit = data.pop('edit', False)
    bot_id = data.pop('bot_id')

    await bot.delete_state(message.from_user.id, message.chat.id)

    if edit:
        path = data.pop('path')
        old_name = db.child(path).get()['name']
        db.child(path).update(data)
        name = data['name']
        positions = db.child(
            f'bots/{message.chat.username}/{bot_id}/positions'
        ).get() or {}

        for position_key, position in positions.items():
            if position.get('category') == old_name:
                db.child(f'bots/{message.chat.username}/{bot_id}/positions/{position_key}').update({'category': name})
    else:
        db.child(f'bots/{message.chat.username}/{bot_id}/categories').push(data)

    return True


@with_db
@with_callback_data
async def category_delete(bot: AsyncTeleBot, call: CallbackQuery, db, data):
    bot_id = data.get('bot_id')
    category_key = data.get('category_key')
    username = call.from_user.username

    category = db.child(f'bots/{username}/{bot_id}/categories/{category_key}').get()['name']

    positions = db.child(f'bots/{username}/{bot_id}/positions/').get()

    for position in positions.values():
        if position.get('category') == category:
            return await bot.send_message(
                call.message.chat.id,
                _('Oops. This category can not be deleted, because it has goods.')
            )

    db.child(f'bots/{username}/{bot_id}/categories/{category_key}').delete()

    return await get_category_list(
        bot,
        bot_id,
        call.message.chat.username,
        call.message,
        _('Category was successfully deleted. What\'s next?')
    )




