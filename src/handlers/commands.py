from telebot.async_telebot import AsyncTeleBot, types
from src.markups.commands import start_markup
from src.messages import START
from src.states import states
from src.utils import gettext as _


async def start(
        bot: AsyncTeleBot,
        message: types.Message = None,
        call: types.CallbackQuery = None,
        msg_text: str = START,
        edit: bool = False
):
    if call:
        message = call.message

    markup = start_markup()

    try:
        return await bot.edit_message_text(
            msg_text,
            message.from_user.id,
            message_id=message.id,
            reply_markup=markup
        )
    except Exception:
        await bot.send_message(
                message.chat.id,
                msg_text,
                reply_markup=markup
        )
        if message.from_user.id == bot.user.id:
            await bot.delete_message(message.chat.id, message_id=message.id)


async def cancel(
        bot: AsyncTeleBot,
        message: types.Message
):
    state = await bot.get_state(message.from_user.id, message.chat.id)
    if not state:
        return await bot.send_message(
            message.chat.id,
            _('No any active command was found.')
        )
    state = state.split(':')[0]
    command = ''

    for st in states:
        if state == st.__name__:
            command = str(st())
            break

    await bot.delete_state(message.from_user.id, message.chat.id)
    return await bot.send_message(
        message.chat.id,
        _('The command {command} has been canceled').format(command=command)
    )
