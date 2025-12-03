import os
import tempfile

from models.storage import Storage


def make_storage():
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, "storage.json")
    return Storage(path=path)


def test_delete_child_removes_tasks_too():
    s = make_storage()

    child_id = s.add_child(
        parent_id=1,
        name="Никита",
        age=8,
        tz_label="Москва",
        tz_offset=3,
    )

    # создаём пару записей заданий этому ребёнку
    s.add_task_record(child_id, 2025, 12, 1, task_id=10)
    s.add_task_record(child_id, 2025, 12, 2, task_id=11)

    # проверка до удаления
    assert s.get_child(child_id) is not None
    assert len(s.get_task_records_for_child(child_id, 2025, 12)) == 2

    # удаляем
    s.delete_child(child_id)

    # ребёнок и его задания должны исчезнуть
    assert s.get_child(child_id) is None
    assert len(s.get_task_records_for_child(child_id, 2025, 12)) == 0
