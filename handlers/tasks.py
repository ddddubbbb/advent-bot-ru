import datetime
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, LabeledPrice
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from models.storage import Storage
from models.task_picker import pick_task, load_tasks
from utils.calendar_logic import is_december
from .start import main_menu_keyboard, today_task_keyboard

router = Router()
storage = Storage()


class TaskStates(StatesGroup):
    waiting_child_for_today_or_reroll = State()
    waiting_child_for_done = State()


def get_child_today(child) -> datetime.date:
    """Локальная дата для ребёнка с учётом tz_offset (часы)."""
    offset = child.get("tz_offset", 0)
    now_utc = datetime.datetime.utcnow()
    local = now_utc + datetime.timedelta(hours=offset)
    return local.date()


def children_choice_keyboard(children):
    """Клавиатура с именами детей и кнопкой назад."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=c["name"])] for c in children] + 
                 [[KeyboardButton(text="⬅ В меню")]],
        resize_keyboard=True
    )

# ---------- ЗАДАНИЕ НА СЕГОДНЯ ----------


@router.message(F.text == "📅 Задание на сегодня")
async def choose_child_for_today(message: Message, state: FSMContext):
    children = storage.get_children_by_parent(message.from_user.id)
    if not children:
        await message.answer(
            "Сначала добавь ребёнка через «👨‍👩‍👧‍👦 Мои дети».",
            reply_markup=main_menu_keyboard()
        )
        return

    if len(children) == 1:
        await send_today_task(message, children[0])
        return

    await state.set_state(TaskStates.waiting_child_for_today_or_reroll)
    await state.update_data(children_ids=[c["id"] for c in children], mode="today")
    await message.answer(
        "Для какого ребёнка дать задание на сегодня?",
        reply_markup=children_choice_keyboard(children)
    )


async def send_today_task(message: Message, child: dict):
    # Локальная дата ребёнка по его часовому поясу
    today = get_child_today(child)

    # Бот вообще работает только в декабре
    if not is_december(today):
        await message.answer(
            "Сейчас не декабрь 🎄\n\n"
            "Можно настроить детей или посмотреть статистику.",
            reply_markup=main_menu_keyboard()
        )
        return

    # Пытаемся найти запись задания на сегодня для этого ребёнка
    rec = storage.get_task_record(
        child_id=child["id"],
        year=today.year,
        month=today.month,
        day=today.day
    )

    # Если запись уже есть
    if rec:
        # Если уже выполнено — просто сообщаем и НЕ показываем текст задания
        if rec.get("status") == "done":
            await message.answer(
                f"✨ Задание на сегодня для {child['name']} уже выполнено.\n"
                f"Приходите завтра за новым заданием! 🎄",
                reply_markup=main_menu_keyboard()
            )
            return

        # Иначе находим связанное задание по task_id
        tasks = load_tasks()
        task = next((t for t in tasks if t["id"] == rec["task_id"]), None)
    else:
        # Записи ещё нет — подбираем новое задание и сохраняем
        task = pick_task(child, today, storage, child["id"])
        storage.add_task_record(
            child_id=child["id"],
            year=today.year,
            month=today.month,
            day=today.day,
            task_id=task["id"]
        )

    if not task:
        await message.answer(
            "Не удалось подобрать задание на сегодня. Попробуй ещё раз позже.",
            reply_markup=main_menu_keyboard()
        )
        return

    text = task["text"].format(name=child["name"])
    await message.answer(
        f"✨ Задание на сегодня для {child['name']}:\n\n{text}",
        reply_markup=today_task_keyboard()
    )

# ---------- ОТМЕТКА «ВЫПОЛНЕНО» ----------


@router.message(F.text == "✅ Выполнено")
async def choose_child_for_done(message: Message, state: FSMContext):
    children = storage.get_children_by_parent(message.from_user.id)
    if not children:
        await message.answer(
            "Сначала добавь ребёнка через «👨‍👩‍👧‍👦 Мои дети».",
            reply_markup=main_menu_keyboard()
        )
        return

    if len(children) == 1:
        await mark_done_for_child(message, children[0])
        return

    await state.set_state(TaskStates.waiting_child_for_done)
    await state.update_data(children_ids=[c["id"] for c in children])
    await message.answer(
        "За какого ребёнка отмечаем задание выполненным?",
        reply_markup=children_choice_keyboard(children)
    )


@router.message(TaskStates.waiting_child_for_done)
async def process_child_for_done(message: Message, state: FSMContext):
    if message.text == "⬅ В меню":
        await state.clear()
        await message.answer("Главное меню:", reply_markup=main_menu_keyboard())
        return

    data = await state.get_data()
    children_ids = data.get("children_ids", [])
    children = storage.get_children_by_parent(message.from_user.id)
    name_to_child = {c["name"]: c for c in children if c["id"] in children_ids}

    child = name_to_child.get(message.text)
    if not child:
        await message.answer("Пожалуйста, выбери одного из детей из списка.")
        return

    await state.clear()
    await mark_done_for_child(message, child)


async def mark_done_for_child(message: Message, child: dict):
    today = get_child_today(child)
    rec = storage.get_task_record(
        child_id=child["id"],
        year=today.year,
        month=today.month,
        day=today.day
    )

    if not rec:
        await message.answer(
            f"У {child['name']} ещё нет задания на сегодня. "
            "Нажми «📅 Задание на сегодня».",
            reply_markup=main_menu_keyboard()
        )
        return

    storage.set_task_status(
        child_id=child["id"],
        year=today.year,
        month=today.month,
        day=today.day,
        status="done"
    )

    await message.answer(
        f"🎉 Круто! Задание для {child['name']} отмечено как выполненное! ✨",
        reply_markup=main_menu_keyboard()
    )

# ---------- ПЛАТНЫЙ REROLL (50 STARS) ----------


@router.message(F.text == "🔄 Перезагрузить задание ⭐")
async def start_reroll(message: Message, state: FSMContext):
    children = storage.get_children_by_parent(message.from_user.id)
    if not children:
        await message.answer(
            "Сначала добавь ребёнка через «👨‍👩‍👧‍👦 Мои дети».",
            reply_markup=main_menu_keyboard()
        )
        return

    if len(children) == 1:
        await send_reroll_invoice(message, children[0])
        return

    await state.set_state(TaskStates.waiting_child_for_today_or_reroll)
    await state.update_data(children_ids=[c["id"] for c in children], mode="reroll")
    await message.answer(
        "Для какого ребёнка перезагрузить задание за 50 Stars?",
        reply_markup=children_choice_keyboard(children)
    )


@router.message(TaskStates.waiting_child_for_today_or_reroll)
async def process_child_for_today_or_reroll(message: Message, state: FSMContext):
    if message.text == "⬅ В меню":
        await state.clear()
        await message.answer("Главное меню:", reply_markup=main_menu_keyboard())
        return

    data = await state.get_data()
    mode = data.get("mode")
    children_ids = data.get("children_ids", [])
    children = storage.get_children_by_parent(message.from_user.id)
    name_to_child = {c["name"]: c for c in children if c["id"] in children_ids}
    child = name_to_child.get(message.text)

    if not child:
        await message.answer("Пожалуйста, выбери одного из детей из списка.")
        return

    await state.clear()

    if mode == "reroll":
        await send_reroll_invoice(message, child)
    else:
        await send_today_task(message, child)


async def send_reroll_invoice(message: Message, child: dict):
    """Формируем платный reroll. Само обновление задания будет в payments.py."""
    today = get_child_today(child)
    payload = f"reload_task_{child['id']}_{today.strftime('%Y%m%d')}"

    await message.answer_invoice(
        title="🔄 Перезагрузить задание",
        description=f"Новое задание для {child['name']} за 50 Stars.",
        payload=payload,
        provider_token="",  # Stars
        currency="XTR",
        prices=[LabeledPrice(label="Reroll задания", amount=50)],
        start_parameter="advent-reroll"
    )


def register_handlers(dp):
    dp.include_router(router)
