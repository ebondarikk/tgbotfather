from telebot.handler_backends import State, StatesGroup
from src.utils import gettext as _


class BotStates(StatesGroup):
    token = State()
    currency = State()
    welcome_text = State()

    def __str__(self):
        return _('Bot updating')


class PositionStates(StatesGroup):
    full = State()
    edit = State()
    bot_id = State()
    name = State()
    price = State()
    image = State()
    description = State()
    category = State()

    def __str__(self):
        return _('Position creating')


class SubItemStates(StatesGroup):
    name = State()

    def __str__(self):
        return _('Sub item creating')


class MailStates(StatesGroup):
    create = State()

    def __str__(self):
        return _('Mail creating')


class CategoryStates(StatesGroup):
    create = State()
    edit = State()
    name = State()

    def __str__(self):
        return _('Category creating')


states = [
    BotStates,
    PositionStates,
    MailStates,
    CategoryStates,
    SubItemStates,
]

