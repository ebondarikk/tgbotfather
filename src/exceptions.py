from src.utils import gettext as _

class BotAlreadyExistsException(Exception):
    def __str__(self):
        return _('Bot with this token is already exists')


class PositionAlreadyExistsException(Exception):
    def __str__(self):
        return _('Position with this name is already exists')
