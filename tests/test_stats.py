import datetime
import os
import tempfile
from unittest.mock import AsyncMock

import pytest
from aiogram import types

from models.storage import Storage
import handlers.stats as stats_module


def make_storage(tmp_path):
    path = os.path.join(tmp_path, "storage.json")
    return Storage(path=path)


def make_message(user_id: int=1, text: str="📊 Статистика") -> types.Message:
    return types.Message(
        message_id=1,
        date=datetime.datetime.now(),
        chat=types.Chat(id=user_id, type="private"),
        from_user=types.User(id=user_id, is_bot=False, first_name="Test"),
        text=text,
    )


@pytest.mark.asyncio
async def test_stats_single_child_done_task(tmp_path):
    storage = make_storage(tmp_path)
    stats_module.storage = storage

    child_id = storage.add_child(
        parent_id=1, name="Никита", age=8, tz_label="Москва", tz_offset=0
    )
    child = storage.get_child(child_id)

    today = datetime.date.today()
    storage.add_task_record(child_id, today.year, today.month, today.day, task_id=1)
    storage.set_task_status(child_id, today.year, today.month, today.day, "done")

    msg = make_message()
    msg.answer = AsyncMock()

    state = AsyncMock()  # для простоты подменим FSM-контекст заглушкой

    await stats_module.stats_entry(msg, state)

    msg.answer.assert_called()
    text = msg.answer.call_args.kwargs["text"]
    assert "Всего заданий выдано: 1" in text
    assert "Выполнено: 1" in text
