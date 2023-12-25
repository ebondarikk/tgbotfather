from src.handlers.bots import (
    bot_list,
    bot_create,
    bot_manage,
    bot_delete,
    bot_deploy,
    bot_schedule_get,
    bot_welcome_text,
    bot_currency_update,
    bot_welcome_text_update
)
from src.handlers.positions import (
    position_list,
    position_create,
    position_manage,
    position_edit,
    position_delete
)

from src.handlers.statistic import (
    statistic_list,
    statistic_revenue,
    statistic_number_of_orders,
    statistic_avg_bill,
    statistic_conversion
)

from src.handlers.mail import (
    mail_list,
    mail_create,
    mail_manage,
    mail_publish
)

from src.handlers.commands import start, help_command
from src.utils import get_hashed_data

ACTIONS = {
    'bot': {
        'list': bot_list,
        'create': bot_create,
        'manage': bot_manage,
        'welcome_text': bot_welcome_text,
        'welcome_text_update': bot_welcome_text_update,
        'currency': bot_currency_update,
        'schedule': bot_schedule_get,
        'deploy': bot_deploy,
        'delete': bot_delete
    },
    'position': {
        'list': position_list,
        'create': position_create,
        'manage': position_manage,
        'edit': position_edit,
        'delete': position_delete
    },
    'statistic': {
        'list': statistic_list,
        'revenue': statistic_revenue,
        'orders_number': statistic_number_of_orders,
        'avg_bill': statistic_avg_bill,
        'conversion': statistic_conversion
    },
    'mail': {
        'list': mail_list,
        'create': mail_create,
        'manage': mail_manage,
        'publish': mail_publish
    },
    'command': {
        'start': start
    },
    'general': {
        'help': help_command
    }
}


def get_action(call):
    data = get_hashed_data(call)
    action = data.get('action')
    return action.split('/'), data


async def callback_router(bot, call):
    action, data = get_action(call)
    if len(action) > 1 and action[0] in ACTIONS.keys():
        return await ACTIONS[action[0]][action[1]](bot=bot, call=call)

