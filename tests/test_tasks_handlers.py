import datetime
import os
import tempfile

import pytest
from unittest.mock import AsyncMock

from aiogram import types
from models.storage import Storage

# Импортируем модуль, где лежат хендлеры задач
import handlers.tasks as tasks_module


def make_storage(tmp_path):
    path = os.path.join(tmp_path, "storage.json")
    return Storage(path=path)


def make_message(user_id: int=1, text: str="test") -> types.Message:
    # Минимальный мок Message для вызова хендлеров напрямую
    return types.Message(
        message_id=1,
        date=datetime.datetime.now(),
        chat=types.Chat(id=user_id, type="private"),
        from_user=types.User(id=user_id, is_bot=False, first_name="Test"),
        text=text,
    )


@pytest.mark.asyncio
async def test_send_today_task_new_record(tmp_path):
    """
    Если записи ещё нет, send_today_task должен создать запись и отправить текст задания.
    """
    storage = make_storage(tmp_path)
    tasks_module.storage = storage

    child_id = storage.add_child(
        parent_id=1, name="Никита", age=8, tz_label="Москва", tz_offset=0
    )
    child = storage.get_child(child_id)

    msg = make_message(text="📅 Задание на сегодня")
    msg.answer = AsyncMock()

    await tasks_module.send_today_task(msg, child)

    # Проверяем, что запись появилась
    today = tasks_module.get_child_today(child)
    rec = storage.get_task_record(child_id, today.year, today.month, today.day)
    assert rec is not None
    assert rec["status"] == "new"

    # Проверяем, что было отправлено сообщение
    msg.answer.assert_called()
    sent_text = msg.answer.call_args.kwargs["text"]
    assert "Задание на сегодня для Никита" in sent_text


@pytest.mark.asyncio
async def test_send_today_task_already_done(tmp_path):
    """
    Если статус уже done, должно прийти сообщение 'уже выполнено, приходите завтра'.
    """
    storage = make_storage(tmp_path)
    tasks_module.storage = storage

    child_id = storage.add_child(
        parent_id=1, name="Леонид", age=6, tz_label="Москва", tz_offset=0
    )
    child = storage.get_child(child_id)
    today = tasks_module.get_child_today(child)

    storage.add_task_record(child_id, today.year, today.month, today.day, task_id=1)
    storage.set_task_status(child_id, today.year, today.month, today.day, "done")

    msg = make_message(text="📅 Задание на сегодня")
    msg.answer = AsyncMock()

    await tasks_module.send_today_task(msg, child)

    msg.answer.assert_called()
    sent_text = msg.answer.call_args.kwargs["text"]
    assert "уже выполнено" in sent_text
    assert "Приходите завтра" in sent_text


@pytest.mark.asyncio
async def test_mark_done_for_child_sets_status(tmp_path):
    """
    mark_done_for_child должен проставлять статус done и присылать подтверждение.
    """
    storage = make_storage(tmp_path)
    tasks_module.storage = storage

    child_id = storage.add_child(
        parent_id=1, name="Никита", age=8, tz_label="Москва", tz_offset=0
    )
    child = storage.get_child(child_id)
    today = tasks_module.get_child_today(child)

    storage.add_task_record(child_id, today.year, today.month, today.day, task_id=1)

    msg = make_message(text="✅ Выполнено")
    msg.answer = AsyncMock()

    await tasks_module.mark_done_for_child(msg, child)

    rec = storage.get_task_record(child_id, today.year, today.month, today.day)
    assert rec["status"] == "done"

    msg.answer.assert_called()
    sent_text = msg.answer.call_args.kwargs["text"]
    assert "отмечено как выполненное" in sent_text


@pytest.mark.asyncio
async def test_send_reroll_invoice_payload(tmp_path):
    """
    send_reroll_invoice должен слать инвойс с правильным payload reload_task_hild_id>_<YYYYMMDD>.
    """
    storage = make_storage(tmp_path)
    tasks_module.storage = storage

    child_id = storage.add_child(
        parent_id=1, name="Никита", age=8, tz_label="Москва", tz_offset=0
    )
    child = storage.get_child(child_id)

    msg = make_message(text="🔄 Перезагрузить задание ⭐")
    msg.answer_invoice = AsyncMock()

    await tasks_module.send_reroll_invoice(msg, child)

    msg.answer_invoice.assert_called()
    kwargs = msg.answer_invoice.call_args.kwargs
    payload = kwargs["payload"]

    assert payload.startswith(f"reload_task_{child_id}_")
    assert kwargs["prices"][0].amount == 50
