import datetime
import re
import uuid

from telebot import types
from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery

from src.states import PositionStates
from src.utils import with_callback_data, with_db, with_bucket, edit_or_resend, step_handler, \
    send_message_with_cancel_markup, gettext as _
from src.markups.positions import positions_list_markup, position_manage_markup


@with_db
async def get_position_list(bot, bot_id, username, message: types.Message, text, db):
    bot_data = db.child(f'bots/{username}/{bot_id}').get()
    positions = bot_data.get('positions', {})
    markup = positions_list_markup(bot_id, bot_data.get('username'), positions)
    await edit_or_resend(bot, message, text or _('Select a good to customize or create a new one'), markup)


@with_callback_data
async def position_list(bot: AsyncTeleBot, call: CallbackQuery, data, message: str = None):
    bot_id = data.get('bot_id')
    return await get_position_list(bot, bot_id, call.from_user.username, call.message, message)


@with_callback_data
@with_db
async def position_pre_create(bot: AsyncTeleBot, call: CallbackQuery, data, db):
    from src.handlers.categories import get_category_list

    bot_id = data.get('bot_id')
    category = data.get('category')
    username = call.from_user.username

    categories = db.child(f'bots/{username}/{bot_id}/categories').get() or None

    if not categories or category is not None:
        return await position_create(bot=bot, call=call, category=category)

    return await get_category_list(
        bot, bot_id, call.from_user.username, call.message, _('Select a category for new position.'), create=1
    )


@with_callback_data
async def position_create(bot: AsyncTeleBot, call: CallbackQuery, data, category=None):
    bot_id = data.get('bot_id')
    await bot.set_state(call.from_user.id, PositionStates.full, call.message.chat.id)

    async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        data['bot_id'] = bot_id
        data['category'] = category

    await bot.send_video(
        call.message.chat.id,
        video=open('instructions/good_create.mov', 'rb'),
        supports_streaming=True
    )
    await send_message_with_cancel_markup(
        bot,
        call.message.chat.id,
        _('Send me a new good with image in next format:\nName\n*Price*\n#Description#')
    )


@with_db
@with_callback_data
@with_bucket
async def position_manage(bot: AsyncTeleBot, call: CallbackQuery, db, data, bucket):
    username = call.from_user.username
    bot_id = data.get('bot_id')
    position_key = data.get('position_key')
    currency = db.child(f'bots/{username}/{bot_id}/currency').get()
    position = db.child(f'bots/{username}/{bot_id}/positions/{position_key}').get()
    img = bucket.blob(position["image"]).download_as_bytes()
    caption = _("""*Name:* _{name}\n_*Price:* _{price} {currency}_\n*Description*: _{description}_\n*Category*: _{category}_""").format(
        name=position['name'],
        price=position['price'],
        description=position.get('description', ''),
        currency=currency,
        category=position.get('category') or _('Other')
    )

    keys_to_edit = (
        ('name', _('name')),
        ('price', _('price')),
        ('description', _('description')),
        ('image', _('image')),
        ('category', _('category'))
    )

    markup = position_manage_markup(bot_id, position_key, position, keys=keys_to_edit)
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
    category = data.get('category')

    path = f'bots/{username}/{bot_id}/positions/{position_key}'

    state = None
    match key_to_edit:
        case 'image':
            state = PositionStates.image
        case 'price':
            state = PositionStates.price
        case 'name':
            state = PositionStates.name
        case 'description':
            state = PositionStates.description

    update_data = {}
    update_data['bot_id'] = bot_id
    update_data['path'] = path
    update_data['edit'] = True

    if state:
        await bot.set_state(call.from_user.id, state, call.message.chat.id)
        async with bot.retrieve_data(call.message.chat.id, call.message.chat.id) as state_data:
            state_data.update(**update_data)

    if key_to_edit == 'category':
        from src.handlers.categories import get_category_list

        if category is None:
            return await get_category_list(
                bot,
                bot_id,
                call.from_user.username,
                call.message,
                _('Select a category for position.'),
                create=0,
                position_key=position_key
            )
        update_data['category'] = category
        return await position_save(bot, call.message, data=update_data)
    else:
        await bot.send_message(call.message.chat.id, _('Send me new {key_to_edit}').format(key_to_edit=key_to_edit))


@with_db
@with_callback_data
async def position_delete(bot: AsyncTeleBot, call: CallbackQuery, db, data):
    bot_id = data.get('bot_id')
    position_key = data.get('position_key')
    username = call.from_user.username
    db.child(f'bots/{username}/{bot_id}/positions/{position_key}').delete()
    await get_position_list(
        bot, bot_id, call.message.chat.username, call.message, text=_('Position was deleted successfully. What\'s next?')
    )



@step_handler
@with_bucket
async def position_full_create_step(message, bot, bucket):
    if message.content_type == 'document' and message.document.mime_type.startswith('image'):
        mime_type = message.document.mime_type
        file_id = message.document.file_id
    elif message.content_type == 'photo':
        mime_type = 'image/jpeg'
        file_id = message.photo[-1].file_id
    else:
        await bot.send_message(
            message.chat.id,
            _('Seems like you forgot attach an image. Try again')
        )
        return

    if not message.caption:
        await bot.send_message(
            message.chat.id,
            _('Seems like you forgot send name and price in description. Try again')
        )
        return

    price_pattern = '\*(\d+\.?\d{1,2}?)\*'

    price_res = re.findall(price_pattern, message.caption)

    if not price_res:
        await bot.send_message(
            message.chat.id,
            _('Seems like price is absent or incorrect. Try like this: *15* or *7.90*')
        )
        return

    price = float(price_res[0])

    name = message.caption.split(f'*{price_res[0]}*')[0].strip().capitalize()

    if not name:
        await bot.send_message(
            message.chat.id,
            _('Seems like you forgot send a name. Try again')
        )
        return

    description = ''
    description_pattern = '#(.*)#'

    description_res = re.findall(description_pattern, message.caption)

    if description_res:
        description = description_res[0]
        if len(description) > 256:
            await bot.send_message(
                message.chat.id,
                _('Description is too large. Max size is 256 symbols')
            )
            return

    file_info = await bot.get_file(file_id)
    photo = await bot.download_file(file_info.file_path)

    format = file_info.file_path.split('.')[-1]
    bucket_path = f'{message.chat.username}/{str(uuid.uuid4())}.{format}'
    blob = bucket.blob(bucket_path)
    blob.upload_from_string(photo, content_type=mime_type)

    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        bot_id = data['bot_id']
        category = data.get('category')

    data = {
        'bot_id': bot_id, 'name': name, 'price': price, 'image': bucket_path, 'description': description,
        'category': category
    }

    return await position_save(bot, message, data=data)


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


@step_handler
async def position_description_step(message, bot):
    if message.content_type != 'text':
        return
    description = message.text

    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        edit = data.get('edit')
        data['description'] = description

    if edit:
        await position_save(bot, message)


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
        bucket_path = f'{message.chat.username}/{str(uuid.uuid4())}.{format}'
        blob = bucket.blob(bucket_path)
        blob.upload_from_string(photo, content_type=mime_type)
        data['image'] = bucket_path

    await position_save(bot, message)


@with_db
async def position_save(bot: AsyncTeleBot, message: types.Message, db, data=None):
    if not data:
        async with bot.retrieve_data(message.chat.id, message.chat.id) as position_data:
            data = position_data

    await bot.delete_state(message.from_user.id, message.chat.id)

    edit = data.pop('edit', False)
    bot_id = data.pop('bot_id', None)
    path = data.pop('path', None)

    if name := data.get('name'):
        positions = db.child('bots').child(message.chat.username).child(bot_id).child('positions').get()
        positions = positions.values() if positions else []
        existing_names = [
            p['name']
            for p in positions
        ]
        if name in existing_names:
            return await bot.send_message(message.chat.id, _('Ooops. Position with this name is already exists'))

    if edit:
        position: dict = db.child(path).get()
        position.update(**data)
        db.child(path).update(position)

        return await get_position_list(
            bot, bot_id, message.chat.username, message, text=_('Position was updated successfully. What\'s next?')
        )

    db.child(f'bots/{message.chat.username}/{bot_id}/positions').push(data)
    db.child(f'bots/{message.chat.username}/{bot_id}').update({'last_updates': str(datetime.datetime.now())})
    return await get_position_list(
        bot, bot_id, message.from_user.username, message, text=_('Position was created successfully. What\'s next?')
    )
