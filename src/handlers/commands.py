from telebot import TeleBot, types
from src.markups.commands import start_markup
from src.messages import START


def start(
        bot: TeleBot,
        message: types.Message = None,
        call: types.CallbackQuery = None,
        msg_text: str = START,
        edit: bool = False
):
    if call:
        message = call.message

    markup = start_markup()

    try:
        return bot.edit_message_text(
            msg_text,
            message.from_user.id,
            message_id=message.id,
            reply_markup=markup
        )
    except Exception:
        bot.send_message(
                message.chat.id,
                msg_text,
                reply_markup=markup
        )
        if message.from_user.id == bot.user.id:
            bot.delete_message(message.chat.id, message_id=message.id)
