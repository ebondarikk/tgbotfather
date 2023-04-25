from telebot.handler_backends import State, StatesGroup


class BotStates(StatesGroup):
    token = State()

    def __str__(self):
        return 'Bot creating'


class PositionStates(StatesGroup):
    edit = State()
    bot_id = State()
    name = State()
    price = State()
    image = State()

    def __str__(self):
        return 'Position creating'


states = [
    BotStates,
    PositionStates
]

