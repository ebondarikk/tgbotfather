from src.handlers.bots import (
    bot_list,
    bot_create,
    bot_manage,
    bot_delete,
    bot_deploy,
    bot_schedule_get,
    bot_welcome_text,
    bot_currency_update,
    bot_welcome_text_update,
    bot_communication
)

from src.handlers.categories import (
    category_list,
    category_create,
    category_manage,
    category_edit,
    category_delete,
)

from src.handlers.positions import (
    position_list,
    position_create_select_category,
    position_pre_create,
    position_manage,
    position_edit,
    position_delete,
    position_freeze,
    subitem_list,
    subitem_create,
    subitem_manage,
    subitem_edit,
    subitem_delete,
    subitem_freeze,
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

from src.handlers.managers import (
    manager_list,
    manager_create,
    manager_manage,
    manager_activate,
    manager_delete
)

from src.handlers.delivery import (
    delivery_manage,
    delivery_condition_manage,
    delivery_activate,
    delivery_cost,
    delivery_min_check,
    delivery_condition
)

from src.handlers.commands import start, help_command, instructions_command, instruction_switch
from src.utils import get_hashed_data

ACTIONS = {
    'bot': {
        'list': bot_list,
        'create': bot_create,
        'manage': bot_manage,
        'welcome_text': bot_welcome_text,
        'welcome_text_update': bot_welcome_text_update,
        'communication': bot_communication,
        'currency': bot_currency_update,
        'schedule': bot_schedule_get,
        'deploy': bot_deploy,
        'delete': bot_delete
    },
    'manager': {
        'list': manager_list,
        'create': manager_create,
        'manage': manager_manage,
        'activate': manager_activate,
        'delete': manager_delete,
    },
    'position': {
        'list': position_list,
        'create': position_create_select_category,
        'pre_create': position_pre_create,
        'manage': position_manage,
        'edit': position_edit,
        'delete': position_delete,
        'freeze': position_freeze,
    },
    'subitem': {
        'list': subitem_list,
        'create': subitem_create,
        'manage': subitem_manage,
        'edit': subitem_edit,
        'delete': subitem_delete,
        'freeze': subitem_freeze
    },
    'category': {
        'list': category_list,
        'create': category_create,
        'manage': category_manage,
        'edit': category_edit,
        'delete': category_delete
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
        'help': help_command,
        'instructions': instructions_command,
        'instruction_switch': instruction_switch
    },
    'delivery': {
        'manage': delivery_manage,
        'condition': delivery_condition_manage,
        'activate': delivery_activate,
        'cost': delivery_cost,
        'min_check': delivery_min_check,
        'set_condition': delivery_condition
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

