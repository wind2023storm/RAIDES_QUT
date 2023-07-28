
from datetime import datetime
from typing import Union
from django.utils.timezone import localdate, localtime, get_current_timezone

"""Date Utility functions relative to the Django Server datetime. Server may be configured with a different timezone."""


def django_local_time(value=None, timezone=get_current_timezone()):
    return localtime(value, timezone)


def next_quarter():
    """Returns the Date starting on the next quarter relative to the Django Server date"""
    local_now = django_local_time().date()
    return datetime(year=local_now.year, month=local_now.month // 4 + 4, day=1)


def next_month():
    """Returns the Date starting on the next month relative to the Django Server date"""
    local_now = django_local_time().date()
    return datetime(year=local_now.year, month=local_now.month + 1, day=1)


def try_get_datetime(date_string: str) -> Union[datetime, None]:
    """Attempts to turn an item into a datetime format as Django localtime, will also attempt to guess the format.

    Parameters
    ----------
        date_string : any
            A datetime string

    Returns
    -------
        datetime, None
            A datetime object as Django localtime or None if the guessing failed
    """
    # Sometimes input may be None, return immediately
    if not date_string:
        return None

    # Use an iterator since they take up less memory than lists
    _formats = iter([
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%dT%H:%M:%S',
        '%d/%m/%Y',
        '%d-%m-%Y',
        '%Y/%m/%d',
        '%Y-%m-%d'
    ])

    for _format in _formats:
        try:
            return datetime.strptime(date_string, _format)
        except (ValueError, TypeError) as e:
            pass

    return None


