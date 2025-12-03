from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from models.storage import Storage
from utils.timezones import get_timezone_labels, get_offset_by_label
from .start import main_menu_keyboard

router = Router()
storage = Storage()


class AddChildStates(StatesGroup):
    waiting_name = State()
    waiting_age = State()
    waiting_tz = State()


class DeleteChildStates(StatesGroup):
    waiting_child_name = State()


def children_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить ребёнка")],
            [KeyboardButton(text="🗑 Удалить")],
            [KeyboardButton(text="⬅ В меню")]
        ],
        resize_keyboard=True
    )


def children_delete_keyboard(children) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=c["name"])] for c in children] + 
                 [[KeyboardButton(text="⬅ В меню")]],
        resize_keyboard=True
    )


@router.message(F.text == "👨‍👩‍👧‍👦 Мои дети")
async def show_children(message: Message, state: FSMContext):
    await state.clear()
    children = storage.get_children_by_parent(message.from_user.id)
    if not children:
        await message.answer(
            "У тебя пока нет детей. Нажми «➕ Добавить ребёнка», чтобы начать.",
            reply_markup=children_menu_keyboard()
        )
        return

    text = "Твои дети:\n"
    for child in children:
        text += f"• {child['name']}, {child['age']} лет — {child['tz_label']}\n"

    await message.answer(
        text,
        reply_markup=children_menu_keyboard()
    )

# ---------- ДОБАВЛЕНИЕ ----------


@router.message(F.text == "➕ Добавить ребёнка")
async def add_child_start(message: Message, state: FSMContext):
    await state.set_state(AddChildStates.waiting_name)
    await message.answer("Как зовут ребёнка? (имя)")


@router.message(AddChildStates.waiting_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AddChildStates.waiting_age)
    await message.answer("Сколько лет? (0–99)")


@router.message(AddChildStates.waiting_age)
async def process_age(message: Message, state: FSMContext):
    try:
        age = int(message.text.strip())
        if not 0 <= age <= 99:
            raise ValueError()
    except ValueError:
        await message.answer("Пожалуйста, введи число от 0 до 99:")
        return

    await state.update_data(age=age)
    tz_labels = get_timezone_labels()
    tz_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=tz)] for tz in tz_labels[:10]] + 
                 [[KeyboardButton(text="⬅ В меню")]],
        resize_keyboard=True
    )
    await state.set_state(AddChildStates.waiting_tz)
    await message.answer("Выбери город/часовой пояс:", reply_markup=tz_keyboard)


@router.message(AddChildStates.waiting_tz)
async def process_tz(message: Message, state: FSMContext):
    if message.text == "⬅ В меню":
        await state.clear()
        await message.answer("Главное меню:", reply_markup=main_menu_keyboard())
        return

    tz_labels = get_timezone_labels()
    if message.text not in tz_labels:
        await message.answer("Пожалуйста, выбери один из вариантов выше:")
        return

    data = await state.get_data()
    name = data["name"]
    age = data["age"]
    tz_label = message.text
    tz_offset = get_offset_by_label(tz_label)

    storage.add_child(
        parent_id=message.from_user.id,
        name=name,
        age=age,
        tz_label=tz_label,
        tz_offset=tz_offset
    )

    await message.answer(
        f"✅ Добавлен: {name}, {age} лет, {tz_label}.\n\n"
        "Декабрь будет волшебным! 🎄✨",
        reply_markup=children_menu_keyboard()
    )
    await state.clear()

# ---------- УДАЛЕНИЕ ----------


@router.message(F.text == "🗑 Удалить")
async def delete_child_start(message: Message, state: FSMContext):
    children = storage.get_children_by_parent(message.from_user.id)
    if not children:
        await message.answer(
            "Список пуст. Сначала добавь кого‑нибудь через «➕ Добавить ребёнка».",
            reply_markup=children_menu_keyboard()
        )
        return

    await state.set_state(DeleteChildStates.waiting_child_name)
    await state.update_data(children_ids=[c["id"] for c in children])
    await message.answer(
        "Кого удалить из списка?",
        reply_markup=children_delete_keyboard(children)
    )


@router.message(DeleteChildStates.waiting_child_name)
async def process_delete_child(message: Message, state: FSMContext):
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
        await message.answer("Пожалуйста, выбери имя из списка.")
        return

    # Удаляем ребёнка и связанные данные
    storage.delete_child(child["id"])

    await state.clear()
    await message.answer(
        f"🗑 «{child['name']}» удалён из списка.",
        reply_markup=children_menu_keyboard()
    )


@router.message(F.text == "⬅ В меню")
async def children_back_to_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_menu_keyboard())


def register_handlers(dp):
    dp.include_router(router)
