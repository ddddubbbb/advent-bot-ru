import datetime


def get_day_type(date: datetime.date) -> str:
    """Возвращает тип дня:
    - "christmas_eve" для 24 декабря
    - "christmas_day" для 25 декабря  
    - "new_year" для 31 декабря
    - "weekend" для субботы/воскресенья
    - "weekday" для остальных дней
    """
    if date.month == 12 and date.day == 24:
        return "christmas_eve"
    if date.month == 12 and date.day == 25:
        return "christmas_day"
    if date.month == 12 and date.day == 31:
        return "new_year"
    if date.weekday() >= 5:
        return "weekend"
    return "weekday"


def is_december(date: datetime.date) -> bool:
    return date.month == 12
