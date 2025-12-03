import datetime
import os
import tempfile
from unittest.mock import AsyncMock, patch

import pytest
from aiogram import types

from models.storage import Storage
import handlers.payments as payments_module
from models import task_picker as task_picker_module


def make_storage(tmp_path):
    path = os.path.join(tmp_path, "storage.json")
    return Storage(path=path)


def make_message(user_id: int=1, payload: str="") -> types.Message:
    return types.Message(
        message_id=1,
        date=datetime.datetime.now(),
        chat=types.Chat(id=user_id, type="private"),
        from_user=types.User(id=user_id, is_bot=False, first_name="Test"),
        successful_payment=types.SuccessfulPayment(
            currency="XTR",
            total_amount=50,
            invoice_payload=payload,
            telegram_payment_charge_id="test",
            provider_payment_charge_id="test2",
        ),
    )


@pytest.mark.asyncio
async def test_successful_payment_reroll_changes_task(tmp_path):
    storage = make_storage(tmp_path)
    payments_module.storage = storage
    task_picker_module.storage = storage  # если он вдруг использует глобальный storage

    # создаём ребёнка и старую задачу
    child_id = storage.add_child(
        parent_id=1, name="Никита", age=8, tz_label="Москва", tz_offset=0
    )
    child = storage.get_child(child_id)
    date_obj = datetime.date(2025, 12, 3)

    storage.add_task_record(child_id, date_obj.year, date_obj.month, date_obj.day, task_id=1)

    # подменяем pick_task, чтобы вернуть новую задачу с id=2
    fake_task = {"id": 2, "text": "Новое тестовое задание для {name}"}

    async def fake_pick_task(child, d, s, cid):
        return fake_task

    with patch("handlers.payments.pick_task", side_effect=fake_pick_task):
        msg = make_message(
            payload=f"reload_task_{child_id}_{date_obj.strftime('%Y%m%d')}"
        )
        msg.answer = AsyncMock()
        msg.answer.text = None
        msg.answer.reply_markup = None
        msg.answer_message = AsyncMock()
        msg.answer_photo = AsyncMock()
        msg.answer_document = AsyncMock()
        msg.answer_video = AsyncMock()
        msg.answer_animation = AsyncMock()
        msg.answer_voice = AsyncMock()
        msg.answer_audio = AsyncMock()
        msg.answer_invoice = AsyncMock()

        # answer мы будем смотреть через call_args
        msg.answer = AsyncMock()

        await payments_module.successful_payment_callback(msg)

        # проверяем, что в storage task_id обновился
        rec = storage.get_task_record(child_id, date_obj.year, date_obj.month, date_obj.day)
        assert rec["task_id"] == 2

        # проверяем, что в ответе есть текст задания и благодарность за 50 Stars
        msg.answer.assert_called()
        text = msg.answer.call_args.kwargs["text"]
        assert "Новое задание для" in text
        assert "Спасибо за 50 Stars" in text
