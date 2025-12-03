import datetime
import os
import tempfile
from unittest.mock import AsyncMock

import pytest
from aiogram import types

from models.storage import Storage
import handlers.payments as payments_module
from models import task_picker as task_picker_module


def make_storage(tmp_path):
    path = os.path.join(tmp_path, "storage.json")
    return Storage(path=path)


def make_message(user_id: int=1) -> types.Message:
    return types.Message(
        message_id=1,
        date=datetime.datetime.now(),
        chat=types.Chat(id=user_id, type="private"),
        from_user=types.User(id=user_id, is_bot=False, first_name="Test"),
        text="test",
    )


@pytest.mark.asyncio
async def test_handle_full_calendar_free_creates_31_days(tmp_path):
    storage = make_storage(tmp_path)
    payments_module.storage = storage
    task_picker_module.storage = storage  # если нужно

    child_id = storage.add_child(
        parent_id=1, name="Никита", age=8, tz_label="Москва", tz_offset=0
    )
    year = 2025

    msg = make_message()
    msg.answer = AsyncMock()

    await payments_module.handle_full_calendar_free(msg, child_id, year)

    # проверяем, что 31 запись для декабря
    records = storage.get_task_records_for_child(child_id, year, 12)
    assert len(records) == 31

    msg.answer.assert_called()
    text = msg.answer.call_args.kwargs["text"]
    assert "ПОЛНЫЙ КАЛЕНДАРЬ" in text
    assert "Никита" in text
