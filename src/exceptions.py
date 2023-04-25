class BotAlreadyExistsException(Exception):
    def __str__(self):
        return 'Bot with this token is already exists'


class PositionAlreadyExistsException(Exception):
    def __str__(self):
        return 'Position with this name is already exists'
