TIMEZONES = [
    {"label": "Москва (UTC+3)", "offset": 3},
    {"label": "Санкт-Петербург (UTC+3)", "offset": 3},
    {"label": "Новосибирск (UTC+7)", "offset": 7},
    {"label": "Екатеринбург (UTC+5)", "offset": 5},
    {"label": "London (UTC+0)", "offset": 0},
    {"label": "New York (UTC-5)", "offset":-5},
]


def get_timezone_labels():
    return [tz["label"] for tz in TIMEZONES]


def get_offset_by_label(label: str) -> int:
    for tz in TIMEZONES:
        if tz["label"] == label:
            return tz["offset"]
    return 0
