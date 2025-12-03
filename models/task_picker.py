import json
import random
from typing import Dict, Any, List
from datetime import date
from pathlib import Path
from config import TASKS_FILE
from utils.calendar_logic import get_day_type


def load_tasks() -> List[Dict[str, Any]]:
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_used_tasks(child_id: int, storage, year: int, month: int=12) -> set:
    """Все использованные task_id за год для ребенка"""
    records = storage.get_child_month_records(child_id, year, month)
    return {r["task_id"] for r in records}


def pick_task(child: Dict[str, Any], date_: date, storage, child_id: int) -> Dict[str, Any]:
    tasks = load_tasks()
    age = child["age"]
    day_type = get_day_type(date_)
    year = date_.year
    
    used_ids = get_used_tasks(child_id, storage, year)
    
    # 1. Точные: возраст + день + не использованные ЭТОТ год
    suitable = [
        t for t in tasks
        if t["min_age"] <= age <= t["max_age"]
        and day_type in t["day_types"]
        and t["id"] not in used_ids
    ]
    
    # 2. Fallback: возраст + день (игнор годовых повторов)
    if not suitable:
        suitable = [t for t in tasks 
                   if t["min_age"] <= age <= t["max_age"] and day_type in t["day_types"]]
    
    # 3. Критический fallback: только возраст
    if not suitable:
        suitable = [t for t in tasks if t["min_age"] <= age <= t["max_age"]]
    
    if not suitable:
        raise ValueError(f"No tasks for age {age}")
    
    return random.choice(suitable)
