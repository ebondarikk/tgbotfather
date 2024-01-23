from telebot.async_telebot import AsyncTeleBot, types
from src.handlers.bots import bot_token_step, bot_welcome_text_updated
from src.handlers.categories import category_create_step
from src.handlers.mail import mail_create_step
from src.handlers.positions import position_name_step, position_price_step, position_image_step, \
    position_full_create_step, position_description_step, subitem_name_step

STEPS = {
    'BotStates': {
        'token': bot_token_step,
        'welcome_text': bot_welcome_text_updated
    },
    'PositionStates': {
        'full': position_full_create_step,
        'name': position_name_step,
        'price': position_price_step,
        'image': position_image_step,
        'description': position_description_step
    },
    'SubItemStates': {
        'name': subitem_name_step,
    },
    'MailStates': {
        'create': mail_create_step
    },
    'CategoryStates': {
        'create': category_create_step,
        'name': category_create_step,
    }
}


async def steps_router(bot: AsyncTeleBot, message: types.Message):
    step = await bot.get_state(message.from_user.id, message.chat.id)
    if not step:
        return

    steps = step.split(':')
    if steps[0] in STEPS:
        return await STEPS[steps[0]][steps[1]](bot=bot, message=message)
