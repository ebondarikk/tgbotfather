import datetime
import json
import math
import uuid

from telebot.async_telebot import types, AsyncTeleBot
from telebot.types import CallbackQuery, InputMediaPhoto, Message

from settings import redis
from src.utils import with_db, with_callback_data, send_message_with_cancel_markup, step_handler, \
    with_bucket, gettext as _, edit_or_resend
from src.markups.mail import mail_list_markup, mail_manage_markup
from src.states import MailStates


@with_db
async def get_mail_list(bot, bot_id, username, message: types.Message, text, db):
    bot_data = db.child(f'bots/{username}/{bot_id}').get()
    mails = bot_data.get('mailings', {})
    markup = mail_list_markup(bot_id, bot_data.get('username'), mails)
    await edit_or_resend(bot, message, text or _('Select a mail to customize or create a new one'), markup)


@with_callback_data
async def mail_list(bot: AsyncTeleBot, call: CallbackQuery, data, message: str = None):
    bot_id = data.get('bot_id')
    return await get_mail_list(bot, bot_id, call.from_user.username, call.message, message)


@with_callback_data
async def mail_create(bot: AsyncTeleBot, call: CallbackQuery, data):
    bot_id = data.get('bot_id')
    await bot.set_state(call.from_user.id, MailStates.create, call.message.chat.id)

    async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        data['bot_id'] = bot_id
        data['mailing_id'] = str(uuid.uuid4())
        data['file_ids'] = []

    await send_message_with_cancel_markup(
        bot,
        call.message.chat.id,
        _('Send a text for mailing or photos with text for mailing')
    )


@with_db
@with_callback_data
@with_bucket
async def mail_manage(bot: AsyncTeleBot, call: CallbackQuery, db, data, bucket):
    username = call.from_user.username
    bot_id = data.get('bot_id')
    mail_key = data.get('mail_key')
    mailing = db.child(f'bots/{username}/{bot_id}/mailings/{mail_key}').get()
    images = mailing.get('images')
    content = mailing.get('html_content') or mailing.get('content')

    markup = mail_manage_markup(bot_id, mail_key, mailing)

    if images:
        img = bucket.blob(images[0]).download_as_bytes()

        await bot.send_photo(
            call.message.chat.id,
            img,
            caption=content,
            parse_mode='HTML',
            reply_markup=markup
        )
    else:
        await bot.send_message(
            call.message.chat.id,
            content,
            parse_mode='HTML',
            reply_markup=markup
        )
    if call.message.from_user.id == bot.user.id:
        await bot.delete_message(call.message.chat.id, message_id=call.message.id)


@with_callback_data
@with_db
@with_bucket
async def mail_publish(bot: AsyncTeleBot, call: CallbackQuery, data, db, bucket):
    username = call.from_user.username
    bot_id = data.get('bot_id')
    mail_key = data.get('mail_key')
    user_bot_data = db.child(f'bots/{username}/{bot_id}').get()
    mailing = user_bot_data['mailings'][mail_key]
    bot_token = user_bot_data['token']

    images = mailing.get('images')
    content = mailing.get('html_content') or mailing.get('content')

    last_published_at = db.child(f'bots/{username}/{bot_id}/last_published_at').get()

    if last_published_at:
        now = datetime.datetime.now()
        published_at = datetime.datetime.fromtimestamp(last_published_at)
        delta = (now - published_at).seconds
        range = 3 * 60 * 60

        if delta < range:
            await bot.send_message(
                call.message.chat.id,
                _('Oops. The next mailing can be sent in {period} minutes').format(period=math.ceil((range - delta) / 60))
            )
        return

    img = None
    user_bot = AsyncTeleBot(bot_token)

    if images:
        img = bucket.blob(images[0]).download_as_bytes()

    users = db.child(f'users/{bot_id}').get() or []
    sent_count = 0

    if not users:
        return await bot.send_message(call.message.chat.id, _('No users to send'))

    for user in users:
        if images:
            await user_bot.send_photo(
                user,
                img,
                caption=content,
                parse_mode='HTML',
            )
        else:
            await user_bot.send_message(
                user,
                content,
                parse_mode='HTML',
            )
        sent_count += 1

    db.child(
        f'bots/{username}/{bot_id}/mailings/{mail_key}'
    ).update(
        {'published_at': datetime.datetime.now().timestamp(), 'published': True}
    )
    db.child(
        f'bots/{username}/{bot_id}'
    ).update({'last_published_at': datetime.datetime.now().timestamp()})

    await bot.send_message(call.message.chat.id, _('Success sent to {cnt} users').format(cnt=sent_count))


@step_handler
@with_bucket
async def mail_create_step(message: Message, bot, bucket):
    file_ids = []

    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        bot_id = data['bot_id']
        mailing_id = data['mailing_id']
        file_ids += list(set(data['file_ids']))

    if message.media_group_id:
        await bot.send_message(
            message.chat.id,
            _('It is allowed to use no more than one photo. Try again')
        )
        return

    if message.content_type == 'document' and message.document.mime_type.startswith('image'):
        mime_type = message.document.mime_type
        file_id = message.document.file_id
        file_ids += [{'id': file_id, 'type': mime_type}]
        content = message.caption
        html_content = message.html_caption

    elif message.content_type == 'photo':
        mime_type = 'image/jpeg'
        file_ids += [{'id': message.photo[-1].file_id, 'type': mime_type}]
        content = message.caption
        html_content = message.html_caption

    elif message.content_type == 'text':
        content = message.text
        html_content = message.html_text
    else:
        await bot.send_message(
            message.chat.id,
            _('Unsupported message format. Please, send me image or text or both.')
        )
        return

    # if len(file_ids) > 2:
    #     await bot.send_message(
    #         message.chat.id,
    #         _('Too much images. Only 2 will be saved')
    #     )
    #     file_ids = file_ids[:2]

    files = []

    for index, file in enumerate(file_ids):
        file_info = await bot.get_file(file['id'])
        photo = await bot.download_file(file_info.file_path)

        format = file_info.file_path.split('.')[-1]
        bucket_path = f'{message.chat.username}/{mailing_id}_{uuid.uuid4()}.{format}'
        blob = bucket.blob(bucket_path)
        blob.upload_from_string(photo, content_type=file['type'])
        files.append(bucket_path)

    data = {
        'bot_id': bot_id,
        'mailing_id': mailing_id,
        'content': content,
        'html_content': html_content,
        'images': files,
        'published': False,
        'created_at': datetime.datetime.now().timestamp()
    }

    return await mailing_save(bot, message, mailing_id, data=data)


@with_db
async def mailing_save(bot: AsyncTeleBot, message: types.Message, mailing_id, db, data):
    await bot.delete_state(message.from_user.id, message.chat.id)
    bot_id = data.pop('bot_id')

    mailings = db.child(f'bots/{message.chat.username}/{bot_id}/mailings').get() or {}

    mailing = [(key, value) for key, value in mailings.items() if value['mailing_id'] == mailing_id]

    if mailing:
        mailing_key, mailing_data = mailing[0]
        mailing_data['images'] = mailing_data.get('images', []) + data.get('images', [])
        db.child(f'bots/{message.chat.username}/{bot_id}/mailings/{mailing_key}').update(mailing_data)
    else:
        db.child(f'bots/{message.chat.username}/{bot_id}/mailings').push(data)

        return await get_mail_list(
            bot,
            bot_id,
            message.from_user.username,
            message,
            text=_('Mailing was created successfully. You can publish it by selecting it below. ')
        )

