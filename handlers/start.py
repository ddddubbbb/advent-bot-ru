from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Задание на сегодня")],
            [KeyboardButton(text="👨‍👩‍👧‍👦 Мои дети")],
            [KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="🎅 Новогодний магазин")],
            [KeyboardButton(text="✉ Обратная связь")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )


def today_task_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Выполнено")],
            [KeyboardButton(text="⬅ В меню")],
        ],
        resize_keyboard=True
    )


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "🎄 Привет! Это адвент-бот для семей с детьми.\n\n"
        "Добавь ребёнка, чтобы получать тёплые задания каждый день декабря. "
        "Задания учитывают возраст и тип дня! ✨\n\n"
        "Премиум-функции и поддержка проекта — в «🎅 Новогодний магазин».",
        reply_markup=main_menu_keyboard()
    )


@router.message(F.text == "⬅ В меню")
async def back_to_main_menu(message: Message):
    await message.answer("Главное меню:", reply_markup=main_menu_keyboard())

# -------- ОБРАТНАЯ СВЯЗЬ --------


FEEDBACK_CHAT_ID = -5024699204  # Feedback-advent-bot-ru


class FeedbackStates(StatesGroup):
    waiting_message = State()


@router.message(F.text == "✉ Обратная связь")
async def feedback_start(message: Message, state: FSMContext):
    await state.set_state(FeedbackStates.waiting_message)
    await message.answer(
        "Напиши одним сообщением, что хочешь передать автору бота. ✨\n\n"
        "Когда отправишь — я анонимно перекину текст в служебный чат."
    )


@router.message(FeedbackStates.waiting_message)
async def feedback_collect(message: Message, state: FSMContext):
    # если по какой-то причине ID не настроен
    if FEEDBACK_CHAT_ID is None:
        await state.clear()
        await message.answer(
            "Обратная связь пока не настроена.",
            reply_markup=main_menu_keyboard()
        )
        return

    text = (
        "📩 Новое сообщение обратной связи:\n\n"
        f"От @{message.from_user.username or 'без_username'} (id={message.from_user.id}):\n\n"
        f"{message.text}"
    )

    # отправляем в приватную группу
    await message.bot.send_message(chat_id=FEEDBACK_CHAT_ID, text=text)

    await state.clear()
    await message.answer(
        "Спасибо! Сообщение передано. 💌",
        reply_markup=main_menu_keyboard()
    )


def register_handlers(dp):
    dp.include_router(router)
