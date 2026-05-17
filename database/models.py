import aiosqlite
from typing import Optional


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: Optional[aiosqlite.Connection] = None

    async def connect(self):
        self.conn = await aiosqlite.connect(self.db_path)
        await self.create_tables()

    async def close(self):
        if self.conn:
            await self.conn.close()

    async def create_tables(self):
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                faculty TEXT,
                course INTEGER,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS faq (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                faculty TEXT,
                course INTEGER,
                category TEXT,
                keywords TEXT
            )
        """)

        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_name TEXT NOT NULL,
                description TEXT,
                phone TEXT,
                email TEXT,
                location TEXT,
                working_hours TEXT,
                category TEXT
            )
        """)

        await self.conn.commit()

    async def get_user(self, user_id: int):
        async with self.conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "user_id": row[0],
                    "username": row[1],
                    "first_name": row[2],
                    "faculty": row[3],
                    "course": row[4],
                    "registered_at": row[5]
                }
            return None

    async def create_user(self, user_id: int, username: str, first_name: str,
                         faculty: str = None, course: int = None):
        await self.conn.execute(
            """INSERT OR REPLACE INTO users
               (user_id, username, first_name, faculty, course)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, username, first_name, faculty, course)
        )
        await self.conn.commit()

    async def update_user_profile(self, user_id: int, faculty: str, course: int):
        await self.conn.execute(
            "UPDATE users SET faculty = ?, course = ? WHERE user_id = ?",
            (faculty, course, user_id)
        )
        await self.conn.commit()

    async def search_faq(self, query: str, faculty: str = None, course: int = None):
        sql = "SELECT question, answer, category FROM faq WHERE 1=1"
        params = []

        if faculty:
            sql += " AND (faculty IS NULL OR faculty = ?)"
            params.append(faculty)

        if course:
            sql += " AND (course IS NULL OR course = ?)"
            params.append(course)

        async with self.conn.execute(sql, params) as cursor:
            return await cursor.fetchall()

    async def get_contacts(self, category: str = None):
        if category:
            sql = "SELECT * FROM contacts WHERE category = ?"
            params = (category,)
        else:
            sql = "SELECT * FROM contacts"
            params = ()

        async with self.conn.execute(sql, params) as cursor:
            rows = await cursor.fetchall()
            return [{
                "id": row[0],
                "service_name": row[1],
                "description": row[2],
                "phone": row[3],
                "email": row[4],
                "location": row[5],
                "working_hours": row[6],
                "category": row[7]
            } for row in rows]

    async def add_faq(self, question: str, answer: str, faculty: str = None,
                     course: int = None, category: str = None, keywords: str = None):
        await self.conn.execute(
            """INSERT INTO faq (question, answer, faculty, course, category, keywords)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (question, answer, faculty, course, category, keywords)
        )
        await self.conn.commit()

    async def add_contact(self, service_name: str, description: str = None,
                         phone: str = None, email: str = None, location: str = None,
                         working_hours: str = None, category: str = None):
        await self.conn.execute(
            """INSERT INTO contacts
               (service_name, description, phone, email, location, working_hours, category)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (service_name, description, phone, email, location, working_hours, category)
        )
        await self.conn.commit()
