import aiosqlite
import os
import uuid
from datetime import date, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "bot.db")


def tomorrow() -> str:
    return (date.today() + timedelta(days=1)).isoformat()


def generate_session_id() -> str:
    return uuid.uuid4().hex[:8]


async def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT NOT NULL,
                username TEXT,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                response TEXT NOT NULL,
                reason TEXT,
                responded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, date)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS poll_sessions (
                session_id TEXT PRIMARY KEY,
                admin_id INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                wait_minutes INTEGER DEFAULT 15
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS poll_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                response TEXT NOT NULL,
                reason TEXT,
                responded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(session_id, user_id)
            )
        """)
        try:
            await db.execute("ALTER TABLE attendance ADD COLUMN reason TEXT")
        except Exception:
            pass
        await db.commit()


async def add_employee(user_id: int, full_name: str, username: str | None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO employees (user_id, full_name, username, is_active) VALUES (?, ?, ?, 1)",
            (user_id, full_name, username),
        )
        await db.commit()


async def remove_employee(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE employees SET is_active = 0 WHERE user_id = ?", (user_id,)
        )
        await db.commit()


async def get_active_employees():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT user_id, full_name, username FROM employees WHERE is_active = 1"
        )
        return await cursor.fetchall()


async def record_attendance(user_id: int, target_date: str, response: str, reason: str | None = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO attendance (user_id, date, response, reason) VALUES (?, ?, ?, ?)",
            (user_id, target_date, response, reason),
        )
        await db.commit()


async def update_attendance_reason(user_id: int, target_date: str, reason: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE attendance SET reason = ? WHERE user_id = ? AND date = ?",
            (reason, user_id, target_date),
        )
        await db.commit()


async def get_unresponded_employees(target_date: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT e.user_id, e.full_name
            FROM employees e
            LEFT JOIN attendance a ON e.user_id = a.user_id AND a.date = ?
            WHERE e.is_active = 1 AND a.id IS NULL
            """,
            (target_date,),
        )
        return await cursor.fetchall()


async def get_today_attendance(target_date: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT e.full_name, e.username, a.response, a.reason
            FROM employees e
            LEFT JOIN attendance a ON e.user_id = a.user_id AND a.date = ?
            WHERE e.is_active = 1
            """,
            (target_date,),
        )
        return await cursor.fetchall()


async def is_employee(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT 1 FROM employees WHERE user_id = ? AND is_active = 1", (user_id,)
        )
        return await cursor.fetchone() is not None


async def get_employee_list():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT user_id, full_name, username FROM employees WHERE is_active = 1 ORDER BY full_name"
        )
        return await cursor.fetchall()


# --- Poll session functions ---

async def create_poll_session(admin_id: int, wait_minutes: int) -> str:
    session_id = generate_session_id()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO poll_sessions (session_id, admin_id, wait_minutes) VALUES (?, ?, ?)",
            (session_id, admin_id, wait_minutes),
        )
        await db.commit()
    return session_id


async def record_poll_response(session_id: str, user_id: int, response: str, reason: str | None = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO poll_responses (session_id, user_id, response, reason) VALUES (?, ?, ?, ?)",
            (session_id, user_id, response, reason),
        )
        await db.commit()


async def update_poll_reason(session_id: str, user_id: int, reason: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE poll_responses SET reason = ? WHERE session_id = ? AND user_id = ?",
            (reason, session_id, user_id),
        )
        await db.commit()


async def get_poll_results(session_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT e.full_name, e.username, pr.response, pr.reason
            FROM employees e
            LEFT JOIN poll_responses pr ON e.user_id = pr.user_id AND pr.session_id = ?
            WHERE e.is_active = 1
            """,
            (session_id,),
        )
        return await cursor.fetchall()
