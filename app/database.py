import aiosqlite
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "bot.db")


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


async def record_attendance(user_id: int, date: str, response: str, reason: str | None = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO attendance (user_id, date, response, reason) VALUES (?, ?, ?, ?)",
            (user_id, date, response, reason),
        )
        await db.commit()


async def update_attendance_reason(user_id: int, date: str, reason: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE attendance SET reason = ? WHERE user_id = ? AND date = ?",
            (reason, user_id, date),
        )
        await db.commit()


async def has_responded_today(user_id: int, date: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT 1 FROM attendance WHERE user_id = ? AND date = ?", (user_id, date)
        )
        return await cursor.fetchone() is not None


async def get_unresponded_employees(date: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT e.user_id, e.full_name
            FROM employees e
            LEFT JOIN attendance a ON e.user_id = a.user_id AND a.date = ?
            WHERE e.is_active = 1 AND a.id IS NULL
            """,
            (date,),
        )
        return await cursor.fetchall()


async def get_today_attendance(date: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT e.full_name, e.username, a.response, a.reason
            FROM employees e
            LEFT JOIN attendance a ON e.user_id = a.user_id AND a.date = ?
            WHERE e.is_active = 1
            """,
            (date,),
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
