import os
import tempfile

import pytest

from models.storage import Storage


def make_storage():
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, "storage.json")
    return Storage(path=path)


def test_add_and_get_child():
    s = make_storage()
    child_id = s.add_child(parent_id=1, name="Никита", age=8,
                           tz_label="Москва", tz_offset=3)
    child = s.get_child(child_id)
    assert child["name"] == "Никита"
    assert child["parent_id"] == 1


def test_task_record_and_status():
    s = make_storage()
    child_id = s.add_child(parent_id=1, name="Тест", age=7,
                           tz_label="Москва", tz_offset=3)
    s.add_task_record(child_id, 2025, 12, 3, task_id=42)
    rec = s.get_task_record(child_id, 2025, 12, 3)
    assert rec["task_id"] == 42
    assert rec["status"] == "new"

    s.set_task_status(child_id, 2025, 12, 3, "done")
    rec2 = s.get_task_record(child_id, 2025, 12, 3)
    assert rec2["status"] == "done"
