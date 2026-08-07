import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_IDS = [8678017540, 6106654173]

TIMEZONE = "Asia/Tashkent"

POLL_HOUR = 9
POLL_MINUTE = 0

REPORT_HOUR = 10
REPORT_MINUTE = 0

MANUAL_POLL_WAIT_MINUTES = 15
