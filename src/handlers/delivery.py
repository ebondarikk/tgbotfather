from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery

from src.markups.delivery import delivery_condition_manage_markup, delivery_manage_markup
from src.states import DeliveryStates
from src.utils import with_db, with_callback_data, gettext as _, edit_or_resend, step_handler

DELIVERY_CONDITIONS = {
    'always_paid': (1, _('Always paid')),
    'paid_and_free_on_min_check': (2,  _('Paid if the minimum check is not reached, then free')),
    'unavailable_and_paid_on_min_check': (3, _('Not available if the minimum check is not reached, then paid')),
    'unavailable_and_free_on_min_check': (4, _('Not available if the minimum check is not reached, then free')),
}

DEFAULT_DELIVERY_DATA = {
    'is_active': False,
    'cost': 0,
    'min_check': 0,
    'condition': 'always_paid'
}


@with_db
async def get_delivery_manage(bot: AsyncTeleBot, bot_id, user_id, message, db, delivery_data=None,):
    if not delivery_data:
        delivery_data = db.child(f'bots/{user_id}/{bot_id}/delivery').get()

    currency = db.child(f'bots/{user_id}/{bot_id}/currency').get()

    is_active = delivery_data.get('is_active', False)
    delivery_cost = delivery_data.get('cost', 0)
    min_check = delivery_data.get('min_check', 0)
    condition = DELIVERY_CONDITIONS[delivery_data.get('condition', 'always_paid')]

    caption = _(
        '*Delivery is active:* {is_active}\n'
        '*Cost of delivery:* {delivery_cost} {currency}\n'
        '*Minimum delivery receipt:* {min_check} {currency}\n'
        '*Delivery condition:* {condition_desc}\n'
    ).format(
        delivery_cost=delivery_cost,
        min_check=min_check,
        currency=currency,
        condition_desc=condition[1],
        is_active=_('Yes') if is_active else _('No')
    )

    markup = delivery_manage_markup(bot_id, user_id, delivery_data)
    return await edit_or_resend(bot, message, caption, markup, parse_mode="Markdown")



@with_db
@with_callback_data
async def delivery_manage(bot: AsyncTeleBot, call: CallbackQuery, db, data):
    user_id = call.from_user.id
    bot_id = data.get('bot_id')
    delivery_data = db.child(f'bots/{user_id}/{bot_id}/delivery').get()

    if not delivery_data:
        db.child(f'bots/{user_id}/{bot_id}/delivery').update(DEFAULT_DELIVERY_DATA)
        delivery_data = DEFAULT_DELIVERY_DATA

    return await get_delivery_manage(bot, bot_id, user_id, call.message, delivery_data=delivery_data)


@with_db
@with_callback_data
async def delivery_condition_manage(bot: AsyncTeleBot, call: CallbackQuery, db, data):
    user_id = call.from_user.id
    bot_id = data.get('bot_id')
    delivery_data = db.child(f'bots/{user_id}/{bot_id}/delivery').get() or {}
    condition = DELIVERY_CONDITIONS[delivery_data.get('condition', 'always_paid')]

    conditions_desc = '\n\t'.join(
        f'{cond[0]} - {cond[1]}' for cond in DELIVERY_CONDITIONS.values()
    )

    caption = _(
        '*Current condition:* _{cond_index}_ - {cond_desc}\n'
        '-----------\n'
        '*Possible conditions:*\n'
        '{conditions_desc}\n'
        '-----------\n'
        'Choose a condition of delivery below:'
    ).format(cond_index=condition[0], cond_desc=condition[1], conditions_desc=conditions_desc)

    markup = delivery_condition_manage_markup(bot_id, DELIVERY_CONDITIONS, condition)
    await edit_or_resend(bot, call.message, caption, markup, parse_mode="Markdown")


@with_db
@with_callback_data
async def delivery_condition(bot: AsyncTeleBot, call: CallbackQuery, db, data):
    user_id = call.from_user.id
    bot_id = data.get('bot_id')
    condition_key = data.get('selected_condition')

    db.child(f'bots/{user_id}/{bot_id}/delivery').update({'condition': condition_key})

    return await get_delivery_manage(bot, bot_id, user_id, call.message)


@with_db
@with_callback_data
async def delivery_activate(bot: AsyncTeleBot, call: CallbackQuery, db, data):
    user_id = call.from_user.id
    bot_id = data.get('bot_id')
    delivery_data = db.child(f'bots/{user_id}/{bot_id}/delivery').get() or {}

    db.child(f'bots/{user_id}/{bot_id}/delivery').update({'is_active': not delivery_data.get('is_active')})

    return await get_delivery_manage(bot, bot_id, user_id, call.message)


@with_db
@with_callback_data
async def delivery_cost(bot: AsyncTeleBot, call: CallbackQuery, db, data):
    user_id = call.from_user.id
    bot_id = data.get('bot_id')
    cost = db.child(f'bots/{user_id}/{bot_id}/delivery/cost').get() or 0
    currency = db.child(f'bots/{user_id}/{bot_id}/currency').get()

    caption = _(
        'Current cost of delivery: {cost} {currency}\n'
        'Send me a new cost (or send 0 to make delivery free)'
    ).format(cost=cost, currency=currency)

    await bot.set_state(call.from_user.id, DeliveryStates.cost, call.message.chat.id)

    async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        data['bot_id'] = bot_id
        data['user_id'] = user_id

    await bot.send_message(call.from_user.id, caption)


@with_db
@with_callback_data
async def delivery_min_check(bot: AsyncTeleBot, call: CallbackQuery, db, data):
    user_id = call.from_user.id
    bot_id = data.get('bot_id')
    min_check = db.child(f'bots/{user_id}/{bot_id}/delivery/min_check').get() or 0
    currency = db.child(f'bots/{user_id}/{bot_id}/currency').get()

    caption = _(
        'Current minimum receipt: {min_check} {currency}\n'
        'Send me a new minimum receipt'
    ).format(min_check=min_check, currency=currency)

    await bot.set_state(call.from_user.id, DeliveryStates.min_check, call.message.chat.id)

    async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        data['bot_id'] = bot_id
        data['user_id'] = user_id

    await bot.send_message(call.from_user.id, caption)


@with_db
@step_handler
async def delivery_cost_step(message, bot, db):
    if message.content_type != 'text':
        return

    try:
        cost = float(message.text)
    except Exception:
        await bot.send_message(message.chat.id, _('please, send me a valid cost'))
        return

    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        bot_id = data.get('bot_id')
        user_id = data.get('user_id')

    db.child(f'bots/{user_id}/{bot_id}/delivery').update({'cost': cost})

    await bot.delete_state(message.from_user.id, message.chat.id)

    return await get_delivery_manage(bot, bot_id, user_id, message)


@with_db
@step_handler
async def delivery_min_check_step(message, bot, db):
    if message.content_type != 'text':
        return

    try:
        min_check = float(message.text)
    except Exception:
        await bot.send_message(message.chat.id, _('please, send me a valid minimum receipt'))
        return

    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        bot_id = data.get('bot_id')
        user_id = data.get('user_id')

    db.child(f'bots/{user_id}/{bot_id}/delivery').update({'min_check': min_check})

    await bot.delete_state(message.from_user.id, message.chat.id)

    return await get_delivery_manage(bot, bot_id, user_id, message)
