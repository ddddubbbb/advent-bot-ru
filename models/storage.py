import json
import os
from typing import Any, Dict, List, Optional


class Storage:

    def __init__(self, path: str="data/storage.json"):
        self.path = path
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            self._save({"children": [], "tasks": []})

    # ---------- ВНУТРЕННИЕ ----------

    def _load(self) -> Dict[str, Any]:
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data: Dict[str, Any]):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ---------- ДЕТИ ----------

    def _next_child_id(self, data: Dict[str, Any]) -> int:
        children = data.get("children", [])
        if not children:
            return 1
        return max(c.get("id", 0) for c in children) + 1

    def add_child(self, parent_id: int, name: str, age: int,
                  tz_label: str, tz_offset: int) -> int:
        data = self._load()
        children = data.get("children", [])
        child_id = self._next_child_id(data)
        children.append({
            "id": child_id,
            "parent_id": parent_id,
            "name": name,
            "age": age,
            "tz_label": tz_label,
            "tz_offset": tz_offset
        })
        data["children"] = children
        self._save(data)
        return child_id

    def get_child(self, child_id: int) -> Optional[Dict[str, Any]]:
        data = self._load()
        for c in data.get("children", []):
            if c.get("id") == child_id:
                return c
        return None

    def get_children_by_parent(self, parent_id: int) -> List[Dict[str, Any]]:
        data = self._load()
        return [c for c in data.get("children", []) if c.get("parent_id") == parent_id]

    def delete_child(self, child_id: int):
        """Удаляет ребёнка и все его задания из хранилища."""
        data = self._load()

        children = data.get("children", [])
        children = [c for c in children if c.get("id") != child_id]
        data["children"] = children

        tasks = data.get("tasks", [])
        tasks = [t for t in tasks if t.get("child_id") != child_id]
        data["tasks"] = tasks

        self._save(data)

    # ---------- ЗАПИСИ ЗАДАНИЙ ПО ДНЯМ ----------

    def _next_task_record_id(self, data: Dict[str, Any]) -> int:
        tasks = data.get("tasks", [])
        if not tasks:
            return 1
        return max(t.get("id", 0) for t in tasks) + 1

    def add_task_record(self, child_id: int, year: int, month: int, day: int, task_id: int):
        data = self._load()
        tasks = data.get("tasks", [])

        rec_id = self._next_task_record_id(data)
        tasks.append({
            "id": rec_id,
            "child_id": child_id,
            "year": year,
            "month": month,
            "day": day,
            "task_id": task_id,
            "status": "new"
        })
        data["tasks"] = tasks
        self._save(data)

    def get_task_record(self, child_id: int, year: int, month: int, day: int) -> Optional[Dict[str, Any]]:
        data = self._load()
        for rec in data.get("tasks", []):
            if (
                rec.get("child_id") == child_id and
                rec.get("year") == year and
                rec.get("month") == month and
                rec.get("day") == day
            ):
                return rec
        return None

    def set_task_status(self, child_id: int, year: int, month: int, day: int, status: str):
        """Обновить статус задания для конкретного ребёнка и даты."""
        data = self._load()
        tasks = data.get("tasks", [])
        for rec in tasks:
            if (
                rec.get("child_id") == child_id and
                rec.get("year") == year and
                rec.get("month") == month and
                rec.get("day") == day
            ):
                rec["status"] = status
        data["tasks"] = tasks
        self._save(data)

    def update_task_id(self, child_id: int, year: int, month: int, day: int, new_task_id: int) -> bool:
        """Используется для reroll: заменить task_id у уже существующей записи."""
        data = self._load()
        updated = False
        tasks = data.get("tasks", [])
        for rec in tasks:
            if (
                rec.get("child_id") == child_id and
                rec.get("year") == year and
                rec.get("month") == month and
                rec.get("day") == day
            ):
                rec["task_id"] = new_task_id
                rec["status"] = "new"
                updated = True
        data["tasks"] = tasks
        self._save(data)
        return updated

    # ---------- ВЫБОРКИ ДЛЯ СТАТИСТИКИ / PICKER ----------

    def get_task_records_for_child(self, child_id: int, year: int, month: int) -> List[Dict[str, Any]]:
        """Вернёт все записи заданий для ребёнка за указанный месяц/год."""
        data = self._load()
        tasks = data.get("tasks", [])
        result = []
        for rec in tasks:
            if (
                rec.get("child_id") == child_id and
                rec.get("year") == year and
                rec.get("month") == month
            ):
                result.append(rec)
        return result

    def get_child_month_records(self, child_id: int, year: int, month: int) -> List[Dict[str, Any]]:
        """
        Совместимость со старым кодом task_picker.py.
        Возвращает те же данные, что и get_task_records_for_child.
        """
        return self.get_task_records_for_child(child_id, year, month)
