# 🎄 Advent Bot RU 

[@novyi_god_advent_bot](https://t.me/novyi_god_advent_bot)

Телеграм‑бот для семей с детьми: каждый день декабря выдаёт тёплые задания, считает прогресс и даёт пару новогодних «плюшек» за Telegram Stars.

## 📁 Структура проекта

```bash
advent-bot-ru/
├─ data/
│  └─ storage.json          # данные детей и заданий
├─ handlers/
│  ├─ start.py              # /start, главное меню, обратная связь
│  ├─ tasks.py              # задания на сегодня, выполнено, reroll
│  ├─ children.py           # добавление/удаление детей
│  ├─ stats.py              # статистика по ребёнку
│  └─ payments.py           # 🎅 Новогодний магазин, Stars, инвойсы
├─ models/
│  ├─ storage.py            # работа с storage.json
│  ├─ task_picker.py        # выбор заданий по правилам
│  └─ timezones.py          # часовые пояса
├─ utils/
│  └─ calendar_logic.py     # проверка «декабрь», работа с датами
├─ tasks_ru.json            # база текстов заданий
├─ tests/
│  ├─ test_storage.py
│  ├─ test_tasks_handlers.py
│  ├─ test_payments_reroll.py
│  ├─ test_payments_calendar.py
│  ├─ test_stats.py
│  ├─ test_children_delete.py
│  ├─ test_task_picker_used_tasks.py
│  ├─ test_main_flow_two_children.py
│  └─ test_shop_menu_texts.py
├─ main.py                  # точка входа бота
├─ requirements.txt
└─ README.md


⚙️ Что умеет бот

- 👨‍👩‍👧‍👦 Несколько детей на одного родителя.
- 🕒 Учет часового пояса ребёнка.
- 📅 «Задание на сегодня» — выдача заданий только в декабре.
- ✅ Отметка выполнения с учётом конкретного ребёнка и дня.
- 📊 Статистика по выбранному ребёнку за месяц.
- 🎅 Новогодний магазин:
  - 🔄 Reroll задания за 50 Stars;
  - 📥 Полный календарь декабря за 100 Stars;
  - 🙏 Донаты 200 / 500 / 1000 Stars.
- ✉ Обратная связь — сообщения улетают в приватный feedback‑чат.
