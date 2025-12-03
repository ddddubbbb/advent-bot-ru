import os
from pathlib import Path

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ENV = os.getenv("ENV", "dev")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required!")

DATA_DIR = Path("./data")
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "storage.json"
TASKS_FILE = DATA_DIR / "tasks_ru.json"
