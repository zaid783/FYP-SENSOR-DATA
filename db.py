# db.py

import aioodbc
from typing import Optional, List, Dict, Any

class Database:
    def __init__(self):
        self.pool: Optional[aioodbc.pool.Pool] = None

    async def connect(self):
        try:
            dsn = (
                "Driver={ODBC Driver 17 for SQL Server};"
                "Server=.;"
                "Database=FSCMS;"
                "Trusted_Connection=yes;"
            )
            self.pool = await aioodbc.create_pool(dsn=dsn, autocommit=True)
            print("✅ Connected to SQL Server database.")
        except Exception as e:
            print("❌ DB connection error:", e)
            raise

    async def disconnect(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            print("🔌 DB connection closed.")

    async def execute(self, query: str, values: tuple = ()):
        if not self.pool:
            raise RuntimeError("Database not connected.")
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(query, values)
                except Exception as e:
                    print(f"🚨 Query failed: {e} | SQL: {query} | VALUES: {values}")
                    raise

    async def fetchall(self, query: str) -> List[Dict[str, Any]]:
        if not self.pool:
            raise RuntimeError("Database not connected.")
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query)
                rows = await cur.fetchall()
                columns = [column[0] for column in cur.description]
                return [dict(zip(columns, row)) for row in rows]


db = Database()
