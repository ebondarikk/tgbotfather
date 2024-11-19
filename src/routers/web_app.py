import json

from src.handlers.bots import bot_schedule_save

ACTIONS = {
    'schedule': bot_schedule_save,
    # 'position_create': position_create_web_app
}


async def web_app_router(bot, message):
    action = json.loads(message.web_app_data.data).get('route')
    if action and action in ACTIONS.keys():
        return await ACTIONS[action](bot=bot, message=message)
