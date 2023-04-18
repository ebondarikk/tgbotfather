from telebot import TeleBot
from telebot.types import CallbackQuery

from src.utils import with_callback_data, with_db, with_bucket, edit_or_resend
from src.markups.positions import positions_list_markup, position_manage_markup


@with_db
@with_callback_data
def position_list(bot: TeleBot, call: CallbackQuery, db, data, message: str = None):
    bot_id = data.get('bot_id')
    username = call.from_user.username
    positions = db.child(f'bots/{username}/{bot_id}/positions').get() or {}
    markup = positions_list_markup(bot_id, positions)
    edit_or_resend(bot, call.message, message or 'Select Position', markup)


@with_callback_data
def position_create(bot: TeleBot, call: CallbackQuery, data):
    bot_id = data.get('bot_id')
    chat_id = call.message.chat.id
    position = {'bot_id': bot_id}
    msg = bot.send_message(call.message.chat.id, 'Set the name for new position')
    bot.register_next_step_handler(msg, process_name_step, position=position, bot=bot)


@with_db
@with_callback_data
@with_bucket
def position_manage(bot: TeleBot, call: CallbackQuery, db, data, bucket):
    username = call.from_user.username
    bot_id = data.get('bot_id')
    position_key = data.get('position_key')
    position = db.child(f'bots/{username}/{bot_id}/positions/{position_key}').get()
    img = bucket.blob(position["image"]).download_as_bytes()
    caption = f"""*Name:* _{position['name']}\n_*Price:* _${position['price']}_"""
    markup = position_manage_markup(bot_id, position_key, position)
    bot.send_photo(
        call.message.chat.id,
        img,
        caption=caption,
        parse_mode="Markdown",
        reply_markup=markup
    )
    if call.message.from_user.id == bot.user.id:
        bot.delete_message(call.message.chat.id, message_id=call.message.id)


@with_callback_data
def position_edit(bot: TeleBot, call: CallbackQuery, data):
    username = call.from_user.username
    bot_id = data.get('bot_id')
    position_key = data.get('position_key')
    key_to_edit = data.get('edit_action')
    path = f'bots/{username}/{bot_id}/positions/{position_key}'

    msg = bot.send_message(call.message.chat.id, f'Send me new {key_to_edit}')
    match key_to_edit:
        case 'image':
            bot.register_next_step_handler(msg, process_image_step, path=path, bot=bot)
        case 'price':
            bot.register_next_step_handler(msg, process_price_step, path=path, bot=bot)
        case 'name':
            bot.register_next_step_handler(msg, process_name_step, path=path, bot=bot)


@with_db
@with_callback_data
def position_delete(bot: TeleBot, call: CallbackQuery, db, data):
    bot_id = data.get('bot_id')
    position_key = data.get('position_key')
    username = call.from_user.username
    db.child(f'bots/{username}/{bot_id}/positions/{position_key}').delete()
    bot.send_message(call.message.chat.id, 'Success')


@with_db
def process_name_step(message, bot, db, path=None, position=None):
    name = message.text
    if path:
        db.child(path).update({'name': name})
        bot.send_message(message.from_user.id, 'success')
    else:
        position['name'] = name
        msg = bot.reply_to(message, 'Now set the price')
        bot.register_next_step_handler(msg, process_price_step, position=position, bot=bot)


@with_db
def process_price_step(message, db, bot, path=None, position=None):
    try:
        price = float(message.text)
    except Exception:
        msg = bot.reply_to(message, 'oops')
        bot.register_next_step_handler(msg, process_price_step, bot=bot)
        return
    if path:
        db.child(path).update({'price': price})
        bot.send_message(message.from_user.id, 'success')
    else:
        position['price'] = price
        msg = bot.reply_to(message, 'Now send me position image')
        bot.register_next_step_handler(msg, process_image_step, position=position, bot=bot)


@with_db
@with_bucket
def process_image_step(message, db, bot, bucket, path=None, position=None):
    if message.content_type == 'document':
        file_id = message.document.file_id
    elif message.content_type == 'photo':
        file_id = message.photo[-1].file_id
    else:
        msg = bot.send_message(
            message.chat.id,
            'This is not an image'
        )
        return bot.register_next_step_handler(msg, process_image_step, bot=bot, path=path, position=position)
    file_info = bot.get_file(file_id)
    photo = bot.download_file(file_info.file_path)

    format = file_info.file_path.split('.')[-1]

    if path:
        name = db.child(path).get()['name']
        bucket_path = f'{message.chat.username}/{name}.{format}'
        blob = bucket.blob(bucket_path)
        blob.upload_from_string(photo)
        db.child(path).update({'image': bucket_path})
        bot.send_message(message.from_user.id, 'success')
        return

    bucket_path = f'{message.chat.username}/{position["name"]}.{format}'
    blob = bucket.blob(bucket_path)
    blob.upload_from_string(photo)
    position['image'] = bucket_path
    bot_id = position.pop('bot_id', None)
    db.child(f'bots/{message.chat.username}/{bot_id}/positions').push(position)
    bot.send_message(message.from_user.id, 'success')
