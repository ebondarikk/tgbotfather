from telebot.async_telebot import AsyncTeleBot, types
from telebot.types import LabeledPrice

from settings import prices
from src.markups.commands import start_markup, instructions_markup
from src.messages import START
from src.states import states
from src.utils import gettext as _, with_db, with_callback_data, edit_or_resend


@with_db
async def start(
        bot: AsyncTeleBot,
        message: types.Message = None,
        call: types.CallbackQuery = None,
        msg_text: str = START,
        parse_mode: str = 'HTML',
        edit: bool = False,
        db=None
):
    if call:
        message = call.message

    markup = start_markup()

    user_data = db.child(f'botly_users/{message.from_user.id}').get()
    if not user_data:
        db.child(f'botly_users/{message.from_user.id}').update({
            'username': message.from_user.username,
            'instructions_enabled': True
        })

    try:
        return await bot.edit_message_text(
            msg_text,
            message.from_user.id,
            parse_mode=parse_mode,
            message_id=message.id,
            reply_markup=markup
        )
    except Exception:
        await bot.send_message(
                message.chat.id,
                msg_text,
                parse_mode=parse_mode,
                reply_markup=markup
        )
        if message.from_user.id == bot.user.id:
            try:
                await bot.delete_message(message.chat.id, message_id=message.id)
            except Exception:
                pass


async def help_command(
        bot: AsyncTeleBot,
        call: types.CallbackQuery
):
    return await bot.send_message(call.message.chat.id, _('To get help, contact with our support @botly_support.'))


@with_db
async def instructions_command(
        bot: AsyncTeleBot,
        call: types.CallbackQuery,
        db
):
    user_id = call.from_user.id
    user_data = db.child(f'botly_users/{user_id}').get()
    instructions_enabled = user_data.get('instructions_enabled')
    markup = instructions_markup(user_id, instructions_enabled=instructions_enabled)
    return await edit_or_resend(
        bot=bot,
        message=call.message,
        text=_('If the Instructions are activated, you will receive video guidance while using the service. '
               'If you don\'t want to receive instructions, turn them off.\nCurrent state of instructions: {state}'
               ).format(state='🔔 ' + _('Enabled') if instructions_enabled else '🔕 ' + _('Disabled')),
        markup=markup

    )


@with_db
@with_callback_data
async def instruction_switch(
        bot: AsyncTeleBot,
        call: types.CallbackQuery,
        db,
        data
):
    instruction_enabled = bool(int(data.get('enable')))
    user_id = call.from_user.id
    db.child(f'botly_users/{user_id}').update({'instructions_enabled': instruction_enabled})

    return await instructions_command(bot, call)


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


async def payment(
        bot: AsyncTeleBot,
        message: types.Message
):
    await bot.send_message(message.chat.id,
                     "Real cards won't work with me, no money will be debited from your account."
                     " Use this test card number to pay for your Time Machine: `4242 4242 4242 4242`"
                     "\n\nThis is your demo invoice:", parse_mode='Markdown')
    # bot.send_invoice()
    return await bot.send_invoice(
        message.chat.id,  # chat_id
        title='Working Time Machine',  # title
        description=' Want to visit your great-great-great-grandparents? Make a fortune at the races? Shake hands with Hammurabi and take a stroll in the Hanging Gardens? Order our Working Time Machine today!',
        invoice_payload='HAPPY FRIDAYS COUPON',  # invoice_payload
        provider_token='381764678:TEST:70142',
        currency='rub',
        prices=prices,  # prices
        photo_url='http://erkelzaar.tsudao.com/models/perrotta/TIME_MACHINE.jpg',
        photo_height=512,  # !=0/None or picture won't be shown
        photo_width=512,
        photo_size=512,
        is_flexible=False,  # True If you need to set up Shipping Fee
        start_parameter='time-machine-example')