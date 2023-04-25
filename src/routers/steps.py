from telebot.async_telebot import AsyncTeleBot, types
from src.handlers.bots import bot_token_step
from src.handlers.positions import position_name_step, position_price_step, position_image_step

STEPS = {
    'BotStates': {
        'token': bot_token_step
    },
    'PositionStates': {
        'name': position_name_step,
        'price': position_price_step,
        'image': position_image_step
    }
}


async def steps_router(bot: AsyncTeleBot, message: types.Message):
    step = await bot.get_state(message.from_user.id, message.chat.id)
    if not step:
        return

    steps = step.split(':')
    if steps[0] in STEPS:
        return await STEPS[steps[0]][steps[1]](bot=bot, message=message)
