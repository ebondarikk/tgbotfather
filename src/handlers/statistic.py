from telebot import types
from telebot.async_telebot import AsyncTeleBot

from src.markups.statistic import statistic_list_markup
from src.utils import with_callback_data, edit_or_resend, with_statistic_period, gettext as _, with_db, get_periods, \
    get_period_orders, get_conversion


async def get_statistic_list(bot, bot_id, message: types.Message, text, bot_username):
    markup = statistic_list_markup(bot_id, bot_username)
    return await edit_or_resend(bot, message, text or _('Select Statistic'), markup)


@with_callback_data
async def statistic_list(bot: AsyncTeleBot, call: types.CallbackQuery, data, message: str = None):
    bot_id = data.get('bot_id')
    return await get_statistic_list(
        bot, bot_id, call.message, message, bot_username=data.get('bot_username')
    )


@with_statistic_period()
@with_db
async def statistic_revenue(bot: AsyncTeleBot, call: types.CallbackQuery, data, db, markup):
    bot_id = data.get('bot_id')
    period = data.get('period')
    orders = db.child(f'orders/{bot_id}').get() or {}
    currency = db.child(f'bots/{call.from_user.id}/{bot_id}/currency').get()
    first_period_orders, second_period_orders = get_period_orders(period, orders)

    current_revenue = str(round(sum(first_period_orders), 2)) + ' ' + str(currency) if first_period_orders else _('No data')
    previous_revenue = str(round(sum(second_period_orders), 2)) + ' ' + str(currency) if second_period_orders else _('No data')

    return await edit_or_resend(
        bot,
        call.message,
        (
            _('{title} for current {period}: {value}\n').format(
                title=_('Revenue'), period=period, value=current_revenue
            ) +
            _('{title} for previous {period}: {value}').format(
                title=_('Revenue'), period=period, value=previous_revenue
            )
        ),
        markup=markup
    )


@with_statistic_period()
@with_db
async def statistic_number_of_orders(bot: AsyncTeleBot, call: types.CallbackQuery, data, db, markup):
    bot_id = data.get('bot_id')
    period = data.get('period')
    orders = db.child(f'orders/{bot_id}').get() or {}

    first_period_orders, second_period_orders = get_period_orders(period, orders)
    current_orders_number = str(len(first_period_orders)) if first_period_orders else _('No data')
    previous_orders_number = str(len(second_period_orders)) if second_period_orders else _('No data')

    return await edit_or_resend(
        bot,
        call.message,
        (
            _('{title} for current {period}: {value}\n').format(
                title=_('Number of orders'), period=period, value=current_orders_number
            ) +
            _('{title} for previous {period}: {value}').format(
                title=_('Number of orders'), period=period, value=previous_orders_number
            )
        ),
        markup=markup
    )


@with_statistic_period()
@with_db
async def statistic_avg_bill(bot: AsyncTeleBot, call: types.CallbackQuery, data, db, markup):
    bot_id = data.get('bot_id')
    period = data.get('period')
    orders = db.child(f'orders/{bot_id}').get() or {}
    currency = db.child(f'bots/{call.from_user.id}/{bot_id}/currency').get()

    first_period_orders, second_period_orders = get_period_orders(period, orders)
    first_period_value = (
        str(round(sum(first_period_orders) / len(first_period_orders), 2)) + ' ' + str(currency) if first_period_orders else _('No data')
    )
    second_period_value = (
        str(round(sum(second_period_orders) / len(second_period_orders), 2)) + ' ' + str(currency) if second_period_orders else _('No data')
    )

    return await edit_or_resend(
        bot,
        call.message,
        (
            _('{title} for current {period}: {value}\n').format(
                title=_('Average bill'), period=period, value=first_period_value
            ) +
            _('{title} for previous {period}: {value}').format(
                title=_('Average bill'), period=period, value=second_period_value
            )
        ),
        markup=markup
    )


@with_db
@with_callback_data
async def statistic_conversion(bot: AsyncTeleBot, call: types.CallbackQuery, data, db):
    bot_id = data.get('bot_id')
    orders = db.child(f'orders/{bot_id}').get() or {}
    users = db.child(f'users/{bot_id}').get() or {}

    conversion = get_conversion(orders, users)

    return await edit_or_resend(
        bot,
        call.message,
        _('CR of your platform is {value}%').format(value=round(conversion, 2)),
        markup=call.message.reply_markup
    )
