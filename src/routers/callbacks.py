from src.handlers.bots import (
    bot_list,
    bot_create,
    bot_manage,
    bot_delete
)
from src.handlers.positions import (
    position_list,
    position_create,
    position_manage,
    position_edit,
    position_delete
)

from src.handlers.commands import start
from src.utils import get_hashed_data

ACTIONS = {
    'bot': {
        'list': bot_list,
        'create': bot_create,
        'manage': bot_manage,
        'delete': bot_delete
    },
    'position': {
        'list': position_list,
        'create': position_create,
        'manage': position_manage,
        'edit': position_edit,
        'delete': position_delete
    },
    'command': {
        'start': start
    }
}


def get_action(call):
    data = get_hashed_data(call)
    action = data.get('action')
    return action.split('/'), data


def callback_router(bot, call):
    action, data = get_action(call)
    if len(action) > 1 and action[0] in ACTIONS.keys():
        return ACTIONS[action[0]][action[1]](bot=bot, call=call)

