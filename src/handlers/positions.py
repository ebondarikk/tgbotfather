from telebot import types
from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery

from src.states import PositionStates
from src.utils import with_callback_data, with_db, with_bucket, edit_or_resend, step_handler, \
    send_message_with_cancel_markup, gettext as _
from src.markups.positions import positions_list_markup, position_manage_markup


@with_db
@with_callback_data
async def position_list(bot: AsyncTeleBot, call: CallbackQuery, db, data, message: str = None):
    bot_id = data.get('bot_id')
    username = call.from_user.username
    bot_data = db.child(f'bots/{username}/{bot_id}').get()
    positions = bot_data.get('positions', {})
    markup = positions_list_markup(bot_id, bot_data.get('username'), positions)
    await edit_or_resend(bot, call.message, message or _('Select Position'), markup)


@with_callback_data
async def position_create(bot: AsyncTeleBot, call: CallbackQuery, data):
    bot_id = data.get('bot_id')
    await bot.set_state(call.from_user.id, PositionStates.name, call.message.chat.id)

    async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        data['bot_id'] = bot_id

    await send_message_with_cancel_markup(
        bot,
        call.message.chat.id,
        _('Set the name for new position')
    )


@with_db
@with_callback_data
@with_bucket
async def position_manage(bot: AsyncTeleBot, call: CallbackQuery, db, data, bucket):
    username = call.from_user.username
    bot_id = data.get('bot_id')
    position_key = data.get('position_key')
    position = db.child(f'bots/{username}/{bot_id}/positions/{position_key}').get()
    img = bucket.blob(position["image"]).download_as_bytes()
    caption = _("""*Name:* _{name}\n_*Price:* _${price}_""").format(
        name=position['name'],
        price=position['price'],
    )
    markup = position_manage_markup(bot_id, position_key, position)
    await bot.send_photo(
        call.message.chat.id,
        img,
        caption=caption,
        parse_mode="Markdown",
        reply_markup=markup
    )
    if call.message.from_user.id == bot.user.id:
        await bot.delete_message(call.message.chat.id, message_id=call.message.id)


@with_callback_data
async def position_edit(bot: AsyncTeleBot, call: CallbackQuery, data):
    username = call.from_user.username
    bot_id = data.get('bot_id')
    position_key = data.get('position_key')
    key_to_edit = data.get('edit_action')
    path = f'bots/{username}/{bot_id}/positions/{position_key}'

    state = None
    match key_to_edit:
        case 'image':
            state = PositionStates.image
        case 'price':
            state = PositionStates.price
        case 'name':
            state = PositionStates.name

    if state:
        await bot.set_state(call.from_user.id, state, call.message.chat.id)
        async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as state_data:
            state_data['bot_id'] = bot_id
            state_data['path'] = path
            state_data['edit'] = True

    await bot.send_message(call.message.chat.id, _('Send me new {key_to_edit}')).format(key_to_edit=key_to_edit)


@with_db
@with_callback_data
async def position_delete(bot: AsyncTeleBot, call: CallbackQuery, db, data):
    bot_id = data.get('bot_id')
    position_key = data.get('position_key')
    username = call.from_user.username
    db.child(f'bots/{username}/{bot_id}/positions/{position_key}').delete()
    await bot.send_message(call.message.chat.id, _('Success'))


@step_handler
async def position_name_step(message, bot):
    if message.content_type != 'text':
        return
    name = message.text

    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        edit = data.get('edit')
        data['name'] = name

    if edit:
        await position_save(bot, message)
    else:
        await bot.set_state(message.from_user.id, PositionStates.price, message.chat.id)
        await bot.send_message(message.from_user.id, _('Now set the price'))


@step_handler
async def position_price_step(message, bot):
    if message.content_type != 'text':
        return

    try:
        price = float(message.text)
    except Exception:
        await bot.send_message(message.chat.id, _('please, send me a valid price'))
        return

    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        edit = data.get('edit')
        data['price'] = price

    if edit:
        await position_save(bot, message)
    else:
        await bot.set_state(message.from_user.id, PositionStates.image, message.chat.id)
        await bot.send_message(message.chat.id, _('Now send me position image'))


@with_db
@with_bucket
@step_handler
async def position_image_step(message, db, bot, bucket):
    mime_type = None
    if message.content_type == 'document' and message.document.mime_type.startswith('image'):
        mime_type = message.document.mime_type
        file_id = message.document.file_id
    elif message.content_type == 'photo':
        mime_type = 'image/jpeg'
        file_id = message.photo[-1].file_id
    else:
        await bot.send_message(
            message.chat.id,
            _('This is not an image')
        )
        return

    file_info = await bot.get_file(file_id)
    photo = await bot.download_file(file_info.file_path)

    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        edit = data.get('edit')

        if edit:
            name = db.child(data.get('path')).get()['name']
        else:
            name = data.get('name')

        format = file_info.file_path.split('.')[-1]
        bucket_path = f'{message.chat.username}/{name}.{format}'
        blob = bucket.blob(bucket_path)
        blob.upload_from_string(photo, content_type=mime_type)
        data['image'] = bucket_path

    await position_save(bot, message)


@with_db
async def position_save(bot: AsyncTeleBot, message: types.Message, db):
    async with bot.retrieve_data(message.from_user.id, message.chat.id) as position_data:
        data = position_data

    await bot.delete_state(message.from_user.id, message.chat.id)

    edit = data.pop('edit', False)
    bot_id = data.pop('bot_id', None)
    path = data.pop('path', None)

    if name := data.get('name'):
        positions = db.child('bots').child(message.from_user.username).child(bot_id).child('positions').get()
        positions = positions.values() if positions else []
        existing_names = [
            p['name']
            for p in positions
        ]
        if name in existing_names:
            return await bot.send_message(message.chat.id, _('Ooops. Position with this name is already exists'))

    if edit:
        db.child(path).update(data)
        return await bot.send_message(message.chat.id, _('Position was edited successfully'))

    db.child(f'bots/{message.chat.username}/{bot_id}/positions').push(data)
    return await bot.send_message(message.chat.id, _('Position was created successfully'))
