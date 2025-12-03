# Импорты всех хендлеров
from . import start, children, tasks, stats, payments


def register_all_handlers(dp):
    start.register_handlers(dp)
    children.register_handlers(dp)
    tasks.register_handlers(dp)
    stats.register_handlers(dp)
    payments.register_handlers(dp)
