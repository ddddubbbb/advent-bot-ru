from __future__ import annotations

import datetime
import json
import random
from typing import Dict, Any, List

from config import TASKS_FILE
from utils.calendar_logic import get_day_type


def load_tasks() -> List[Dict[str, Any]]:
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def pick_task(child: Dict[str, Any], date: datetime.date, used_task_ids: List[int]) -> Dict[str, Any]:
    tasks = load_tasks()
    age = child["age"]
    day_type = get_day_type(date)
    suitable = [
        t
        for t in tasks
        if t["min_age"] <= age <= t["max_age"]
        and day_type in t["day_types"]
        and t["id"] not in used_task_ids
    ]

    if not suitable:
        suitable = [t for t in tasks if t["min_age"] <= age <= t["max_age"]]

    if not suitable:
        raise ValueError("No tasks available for this age and day type")

    return random.choice(suitable)
