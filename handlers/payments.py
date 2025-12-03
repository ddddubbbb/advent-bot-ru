import datetime
from aiogram import Router, F
from aiogram.types import (
    Message, PreCheckoutQuery, LabeledPrice,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from models.storage import Storage
from models.task_picker import pick_task, load_tasks
from .start import main_menu_keyboard, today_task_keyboard

router = Router()
storage = Storage()

# Цены в Stars
STAR_PRICE_REROLL = 50  # перезагрузка задания
STAR_PRICE_FULL_CAL = 100  # календарь на месяц
DONATION_PACKS = [200, 500, 1000]


class ShopStates(StatesGroup):
    waiting_child_for_reroll = State()
    waiting_child_for_calendar = State()

# -------- ГЛАВНОЕ МЕНЮ МАГАЗИНА --------


@router.message(F.text == "🎅 Новогодний магазин")
async def santa_shop_menu(message: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔄 Обновить задание ⭐50")],
            [KeyboardButton(text="📥 Календарь на месяц ⭐100")],
            [KeyboardButton(text="🙏 Поддержать проект")],
            [KeyboardButton(text="⬅ В меню")],
        ],
        resize_keyboard=True
    )
    await message.answer(
        "🎅 Добро пожаловать в Новогодний магазин!\n\n"
        "🔄 Обновить задание — получить новое задание на сегодня за 50 Stars.\n"
        "📥 Календарь на месяц — открыть все задания декабря для выбранного ребёнка за 100 Stars.\n"
        "🙏 Поддержать проект — донат на развитие (200 / 500 / 1000 Stars).",
        reply_markup=kb
    )


def children_keyboard(children):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=c["name"])] for c in children] + 
                 [[KeyboardButton(text="⬅ В меню")]],
        resize_keyboard=True
    )

# -------- REROLL ЗАДАНИЯ (50) --------


@router.message(F.text == "🔄 Обновить задание ⭐50")
async def reroll_start(message: Message, state: FSMContext):
    children = storage.get_children_by_parent(message.from_user.id)
    if not children:
        await message.answer(
            "Сначала добавь ребёнка через «👨‍👩‍👧‍👦 Мои дети».",
            reply_markup=main_menu_keyboard()
        )
        return

    # один ребёнок — сразу инвойс
    if len(children) == 1:
        await send_reroll_invoice(message, children[0])
        return

    # несколько детей — выбор имени через FSM
    await state.set_state(ShopStates.waiting_child_for_reroll)
    await state.update_data(children_ids=[c["id"] for c in children])
    await message.answer(
        "Для какого ребёнка перезагрузить задание за 50 Stars?",
        reply_markup=children_keyboard(children)
    )


@router.message(ShopStates.waiting_child_for_reroll)
async def reroll_choose_child(message: Message, state: FSMContext):
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

    await state.clear()
    await send_reroll_invoice(message, child)


async def send_reroll_invoice(message: Message, child: dict):
    # дата по часовому поясу ребёнка здесь не нужна, берём календарный сегодня
    today = datetime.date.today()
    payload = f"reload_task_{child['id']}_{today.strftime('%Y%m%d')}"

    await message.answer_invoice(
        title="🔄 Перезагрузить задание",
        description=f"Новое задание для {child['name']} за 50 Stars.",
        payload=payload,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Reroll задания", amount=STAR_PRICE_REROLL)],
        start_parameter="advent-reroll"
    )

# -------- КАЛЕНДАРЬ НА МЕСЯЦ (100) --------


@router.message(F.text == "📥 Календарь на месяц ⭐100")
async def full_calendar_start(message: Message, state: FSMContext):
    children = storage.get_children_by_parent(message.from_user.id)
    if not children:
        await message.answer(
            "Сначала добавь ребёнка через «👨‍👩‍👧‍👦 Мои дети».",
            reply_markup=main_menu_keyboard()
        )
        return

    if len(children) == 1:
        await send_full_calendar_invoice(message, children[0])
        return

    await state.set_state(ShopStates.waiting_child_for_calendar)
    await state.update_data(children_ids=[c["id"] for c in children])
    await message.answer(
        "Для какого ребёнка открыть календарь на месяц за 100 Stars?",
        reply_markup=children_keyboard(children)
    )


@router.message(ShopStates.waiting_child_for_calendar)
async def full_calendar_choose_child(message: Message, state: FSMContext):
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

    await state.clear()
    await send_full_calendar_invoice(message, child)


async def send_full_calendar_invoice(message: Message, child: dict):
    year = datetime.date.today().year
    payload = f"full_calendar_{child['id']}_{year}"

    # --- DEBUG-ЗАГЛУШКА БЕСПЛАТНО ---
    # Чтобы БЕСПЛАТНО протестировать вид календаря:
    # 1) закомментируй блок answer_invoice ниже
    # 2) раскомментируй 4 строки handle_full_calendar_free(...)
    #     "Это БЕСПЛАТНЫЙ тест календаря (оплата отключена в коде).",
    # await handle_full_calendar_free(message, child['id'], year)
    # await message.answer(
    #     reply_markup=main_menu_keyboard()
    # )
    # return
    # --- КОНЕЦ ЗАГЛУШКИ ---

    await message.answer_invoice(
        title="📥 Календарь на месяц",
        description=f"Все задания декабря для {child['name']}.",
        payload=payload,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Календарь на месяц", amount=STAR_PRICE_FULL_CAL)],
        start_parameter="advent-full-calendar"
    )


async def handle_full_calendar_free(message: Message, child_id: int, year: int):
    """Фактическая генерация календаря (платёж/бесплатно — решается выше)."""
    child = storage.get_child(child_id)
    if not child:
        await message.answer("Ошибка: ребёнок не найден.", reply_markup=main_menu_keyboard())
        return

    tasks = load_tasks()
    calendar_text = f"🎄 ПОЛНЫЙ КАЛЕНДАРЬ {year} ДЛЯ {child['name']}:\n\n"

    for day in range(1, 32):
        date_ = datetime.date(year, 12, day)
        rec = storage.get_task_record(child_id, year, 12, day)

        if not rec:
            task = pick_task(child, date_, storage, child_id)
            storage.add_task_record(child_id, year, 12, day, task["id"])
            rec = storage.get_task_record(child_id, year, 12, day)

        task = next((t for t in tasks if t["id"] == rec["task_id"]), None)
        status = "✅" if rec["status"] == "done" else "⏳"
        calendar_text += f"{day:2d}. {status} {task['text'].format(name=child['name'])}\n"

    await message.answer(calendar_text, reply_markup=main_menu_keyboard())

# -------- ДОНАТЫ (200 / 500 / 1000) --------


@router.message(F.text == "🙏 Поддержать проект")
async def donation_menu(message: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⭐ 200 Stars"), KeyboardButton(text="⭐ 500 Stars")],
            [KeyboardButton(text="⭐ 1000 Stars")],
            [KeyboardButton(text="⬅ В меню")],
        ],
        resize_keyboard=True
    )
    await message.answer(
        "Выбери сумму поддержки проекта 🙏:",
        reply_markup=kb
    )


def parse_donation_amount(text: str) -> int | None:
    try:
        parts = text.split()
        for p in parts:
            if p.isdigit():
                return int(p)
    except Exception:
        return None
    return None


@router.message(F.text.startswith("⭐ ") & F.text.endswith("Stars"))
async def process_donation(message: Message):
    amount = parse_donation_amount(message.text)
    if not amount or amount not in DONATION_PACKS:
        await message.answer(
            "Не понял сумму. Выбери одну из предложенных кнопок.",
            reply_markup=main_menu_keyboard()
        )
        return

    await message.answer_invoice(
        title="🙏 Поддержка проекта",
        description="Добровольная поддержка адвент-бота.",
        payload=f"donation_{amount}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=f"Поддержать на {amount} Stars", amount=amount)],
        start_parameter="advent-donation"
    )

# -------- ПЛАТЁЖИ --------


@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_q: PreCheckoutQuery):
    await pre_checkout_q.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment_callback(message: Message):
    payload = message.successful_payment.invoice_payload

    # REROLL
    if payload.startswith("reload_task_"):
        parts = payload.split("_")
        child_id = int(parts[2])
        date_str = "_".join(parts[3:])
        date_obj = datetime.datetime.strptime(date_str, "%Y%m%d").date()

        child = storage.get_child(child_id)
        if not child:
            await message.answer(
                "Ошибка: ребёнок не найден.",
                reply_markup=main_menu_keyboard()
            )
            return

        new_task = pick_task(child, date_obj, storage, child_id)
        storage.update_task_id(
            child_id=child_id,
            year=date_obj.year,
            month=date_obj.month,
            day=date_obj.day,
            new_task_id=new_task["id"]
        )

        text = new_task["text"].format(name=child["name"])
        await message.answer(
            f"✨ Магия сработала! Новое задание для {child['name']}:\n\n{text}\n\n"
            "⭐ Спасибо за 50 Stars!",
            reply_markup=today_task_keyboard()
        )
        return

    # ПОЛНЫЙ КАЛЕНДАРЬ
    if payload.startswith("full_calendar_"):
        parts = payload.split("_")
        child_id = int(parts[2])
        year = int(parts[3])
        await handle_full_calendar_free(message, child_id, year)
        await message.answer(
            "⭐ Спасибо за 100 Stars! Календарь на месяц открыт. 🎄",
            reply_markup=main_menu_keyboard()
        )
        return

    # ДОНАТЫ
    if payload.startswith("donation_"):
        amount = int(payload.split("_")[1])
        await message.answer(
            f"🙏 Спасибо за поддержку на {amount} Stars! "
            "Ты помогаешь делать декабрь ещё теплее. 🎄",
            reply_markup=main_menu_keyboard()
        )
        return

    await message.answer(
        "⭐ Спасибо за поддержку проекта! 🎄",
        reply_markup=main_menu_keyboard()
    )


@router.message(F.text == "⬅ В меню")
async def back_to_menu(message: Message):
    await message.answer("Главное меню:", reply_markup=main_menu_keyboard())


def register_handlers(dp):
    dp.include_router(router)
