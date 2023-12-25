from enum import Enum
from src.utils import gettext as _


class StatisticPeriodEnum(Enum):
    day = _('Day')
    three_days = _('3 days')
    week = _('Week')
    two_weeks = _('2 weeks')
    month = _('Month')
    two_months = _('2 months')
    three_months = _('3 months')
    half_year = _('Half-year')
    year = _('Year')
