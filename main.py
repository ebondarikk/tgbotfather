import json

import firebase_admin
import telebot
from firebase_admin import credentials, storage, db as firebase_db
from telebot import types
from telebot.types import WebAppInfo, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from firebase import firebase

bot_token = '6005647989:AAHhMz5CSVrjAAhEhJECUV5nIcxrwVp57QM'
bot = telebot.TeleBot(bot_token)
hi_msg = """
I can help you create and manage your Tebots.
"""

hashed = {}

position_dict = {}

cred = credentials.Certificate("telegram-bot-1-c1cfe-firebase-adminsdk-yef1j-ca269c84ad.json")
firebase_admin.initialize_app(
    cred,
    {
        'storageBucket': 'telegram-bot-1-c1cfe.appspot.com',
        'databaseURL': 'https://telegram-bot-1-c1cfe-default-rtdb.firebaseio.com/'
    }
)
bucket = storage.bucket()
db = firebase_db.reference()


class Position:
    def __init__(self, bot_id):
        self.bot_id = bot_id
        self.name = None
        self.price = None
        self.image = None

    def to_dict(self):
        return {'name': self.name, 'price': self.price, 'image': self.image}


def action(action_name, **kwargs):
    if action_name == 'manageposition':
        pass
    if kwargs:
        key = hex(hash(json.dumps(kwargs)))
        hashed[key] = kwargs
    data = json.dumps({'action': action_name, **kwargs})
    return data


def check_action(call, action):
    data = json.loads(call.data)
    return data.get('action') == action


def back_menu_option(back_to, **kwargs):
    return [InlineKeyboardButton('<< Back', callback_data=action(back_to, **kwargs))]


@bot.message_handler(commands=['start', 'help'])
@bot.callback_query_handler(func=lambda call: check_action(call, 'start'))
def start(message, msg_text=hi_msg, edit=False):
    main_menu = [
        [InlineKeyboardButton('My Bots', callback_data=action('mybots'))]
    ]
    markup = InlineKeyboardMarkup(main_menu)
    if edit:
        bot.edit_message_text(
            msg_text,
            message.from_user.id,
            message_id=message.id,
            reply_markup=markup
        )
    else:
        bot.send_message(
            message.from_user.id,
            msg_text,
            reply_markup=markup
        )


@bot.callback_query_handler(func=lambda call: check_action(call, 'createnewbot'))
def createnewbot(call):
    cancel_btn = KeyboardButton('cancel')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(cancel_btn)
    msg = bot.edit_message_text(
        'Create a new bot via BotFather and send me a token',
        call.from_user.id,
        message_id=call.message.id,
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, create_bot_step)


def create_bot_step(message):
    token = message.text
    if token == 'cancel':
        start(message, edit=True)
        return
    newbot = telebot.TeleBot(token)
    try:
        username = newbot.user.username
        fullname = newbot.user.full_name
        bot_id = newbot.user.id
    except telebot.apihelper.ApiException:
        bot.send_message(message.from_user.id, 'Invalid bot token')
        createnewbot(message)
    else:
        db.child('bots').child(message.from_user.username).child(str(bot_id)).update(
            {'username': username, 'fullname': fullname, 'token': token}
        )
        success_msg = f'Tebot {fullname} was created successfully'
        start(message, msg_text=success_msg, edit=True)


@bot.callback_query_handler(func=lambda call: check_action(call, 'mybots'))
def mybots(call):
    username = call.from_user.username
    bots = db.child('bots').child(username).get() or {}

    bots_menu = [
        [InlineKeyboardButton('Create new TeBot', callback_data=action('createnewbot'))],
        *[
            [InlineKeyboardButton(f'{index + 1}. {bot_data["fullname"]}', callback_data=action('managebot', bot_id=bot_id))
             for index, (bot_id, bot_data) in enumerate(bots.items())]
        ],
        back_menu_option('start')
    ]
    markup = InlineKeyboardMarkup(bots_menu)
    bot.edit_message_text('Select TeBot to manage', call.from_user.id, message_id=call.message.id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: check_action(call, 'managebot'))
def manage_bot(call):
    data = json.loads(call.data)
    manage_menu = [
        [InlineKeyboardButton('Positions', callback_data=action('positions_list', bot_id=data['bot_id']))],
        [InlineKeyboardButton('Remove TeBot', callback_data=action('deletebot', bot_id=data['bot_id']))],
        back_menu_option('mybots')
    ]
    markup = InlineKeyboardMarkup(manage_menu)
    bot.edit_message_text('Select Action', call.from_user.id, message_id=call.message.id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: check_action(call, 'positions_list'))
def positions_list(call):
    data = json.loads(call.data)
    bot_id = data.get('bot_id')
    username = call.from_user.username
    positions = db.child(f'bots/{username}/{bot_id}/positions').get() or {}
    positions_menu = [
        [InlineKeyboardButton('Create a new position', callback_data=action('newitem', bot_id=data['bot_id']))],
        *[
            [InlineKeyboardButton(
                f'{index + 1}. {position_data["name"]}',
                callback_data=action('manageposition', bot_id=bot_id, position_key=position_key)
            )
             for index, (position_key, position_data) in enumerate(positions.items())]
        ],
        back_menu_option('managebot', bot_id=bot_id)
    ]
    markup = InlineKeyboardMarkup(positions_menu)
    bot.edit_message_text('Select Position', call.from_user.id, message_id=call.message.id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: check_action(call, 'manageposition'))
def manage_position(call):
    data = json.loads(call.data)
    username = call.from_user.username
    bot_id = data.get('bot_id')
    position_key = data.get('position_key')
    position = db.child(f'bots/{username}/{bot_id}/positions/{position_key}').get()
    pass


@bot.callback_query_handler(func=lambda call: check_action(call, 'deletebot'))
def delete_bot(call):
    data = json.loads(call.data)
    bot_id = data.get('bot_id')
    username = call.from_user.username
    db.child(f'bots/{username}/{bot_id}').set({})
    bot.send_message(call.from_user.id, 'Success')


@bot.callback_query_handler(func=lambda call: check_action(call, 'newitem'))
def newitem(call):
    data = json.loads(call.data)
    bot_id = data.get('bot_id')
    chat_id = call.from_user.id
    position = Position(bot_id=bot_id)
    position_dict[chat_id] = position
    msg = bot.send_message(call.from_user.id, 'Set the name for new position')
    bot.register_next_step_handler(msg, process_name_step)


def process_name_step(message):
    chat_id = message.chat.id
    name = message.text
    position = position_dict[chat_id]
    position.name = name
    msg = bot.reply_to(message, 'Now set the price')
    bot.register_next_step_handler(msg, process_price_step)


def process_price_step(message):
    try:
        price = float(message.text)
    except Exception:
        msg = bot.reply_to(message, 'oops')
        bot.register_next_step_handler(msg, process_price_step)
        return
    chat_id = message.chat.id
    position = position_dict[chat_id]
    position.price = price
    msg = bot.reply_to(message, 'Now send me position image')
    bot.register_next_step_handler(msg, process_image_step)


def process_image_step(message):
    chat_id = message.chat.id
    position = position_dict[chat_id]
    if message.content_type == 'document':
        file_id = message.document.file_id
    elif message.content_type == 'photo':
        file_id = message.photo[-1].file_id
    file_info = bot.get_file(file_id)
    print('getting photo...')
    photo = bot.download_file(file_info.file_path)
    format = file_info.file_path.split('.')[-1]
    bucket_path = f'{message.chat.username}/{position.name}.{format}'
    blob = bucket.blob(bucket_path)
    print('uploading')
    blob.upload_from_string(photo)
    position.image = bucket_path
    db.child(f'bots/{message.chat.username}/{position.bot_id}/positions').push(position.to_dict())
    bot.send_message(message.from_user.id, 'success')


bot.polling(none_stop=True, interval=0)
