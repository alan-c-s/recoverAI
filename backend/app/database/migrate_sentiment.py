import asyncio
from sqlalchemy import text
from app.database.session import engine


async def migrate_sqlite_columns():
    print("Running SQLite ALTER TABLE migration for sentiment columns...")
    async with engine.begin() as conn:
        try:
            await conn.execute(
                text(
                    "ALTER TABLE recovery_checkins ADD COLUMN sentiment_label VARCHAR(50) DEFAULT 'Neutral'"
                )
            )
            print("Added column sentiment_label to recovery_checkins")
        except Exception as e:
            print("Column sentiment_label note:", e)

        try:
            await conn.execute(
                text(
                    "ALTER TABLE recovery_checkins ADD COLUMN sentiment_score FLOAT DEFAULT 0.0"
                )
            )
            print("Added column sentiment_score to recovery_checkins")
        except Exception as e:
            print("Column sentiment_score note:", e)

    print("✅ Migration complete!")


if __name__ == "__main__":
    asyncio.run(migrate_sqlite_columns())
