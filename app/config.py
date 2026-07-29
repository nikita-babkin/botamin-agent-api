import os
from pathlib import Path
from zoneinfo import ZoneInfo


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BOOKINGS_FILE = DATA_DIR / "bookings.jsonl"

MSK = ZoneInfo("Europe/Moscow")
API_KEY = os.getenv("BOTAMIN_API_KEY")

if not API_KEY:
    raise RuntimeError("Переменная окружения BOTAMIN_API_KEY не настроена")
