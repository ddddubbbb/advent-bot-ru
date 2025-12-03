import datetime
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from models.storage import Storage
from .start import main_menu_keyboard

router = Router()
storage = Storage()


class StatsStates(StatesGroup):
    waiting_child_for_stats = State()


def stats_children_keyboard(children):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=c["name"])] for c in children] + 
                 [[KeyboardButton(text="⬅ В меню")]],
        resize_keyboard=True
    )


def build_stats_text(child, year, month):
    records = storage.get_task_records_for_child(child["id"], year, month)
    total = len(records)
    done = sum(1 for r in records if r.get("status") == "done")
    in_progress = total - done

    month_name = "декабрь" if month == 12 else str(month)
    return (
        f"📊 Статистика для {child['name']} за {month_name} {year} года:\n\n"
        f"Всего заданий выдано: {total}\n"
        f"✅ Выполнено: {done}\n"
        f"⏳ В процессе: {in_progress}"
    )


@router.message(F.text == "📊 Статистика")
async def stats_entry(message: Message, state: FSMContext):
    children = storage.get_children_by_parent(message.from_user.id)
    if not children:
        await message.answer(
            "Сначала добавь ребёнка через «👨‍👩‍👧‍👦 Мои дети».",
            reply_markup=main_menu_keyboard()
        )
        return

    today = datetime.date.today()
    year, month = today.year, today.month

    if len(children) == 1:
        text = build_stats_text(children[0], year, month)
        await message.answer(text, reply_markup=main_menu_keyboard())
        return

    await state.set_state(StatsStates.waiting_child_for_stats)
    await state.update_data(children_ids=[c["id"] for c in children], year=year, month=month)
    await message.answer(
        "Для кого показать статистику?",
        reply_markup=stats_children_keyboard(children)
    )


@router.message(StatsStates.waiting_child_for_stats)
async def stats_choose_child(message: Message, state: FSMContext):
    if message.text == "⬅ В меню":
        await state.clear()
        await message.answer("Главное меню:", reply_markup=main_menu_keyboard())
        return

    data = await state.get_data()
    children_ids = data.get("children_ids", [])
    year = data.get("year")
    month = data.get("month")

    children = storage.get_children_by_parent(message.from_user.id)
    name_to_child = {c["name"]: c for c in children if c["id"] in children_ids}
    child = name_to_child.get(message.text)

    if not child:
        await message.answer("Пожалуйста, выбери имя из списка.")
        return

    text = build_stats_text(child, year, month)
    await state.clear()
    await message.answer(text, reply_markup=main_menu_keyboard())


def register_handlers(dp):
    dp.include_router(router)
