"""
Vex - Database Engine & Session Management
Async SQLAlchemy setup for PostgreSQL
"""
import os
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text

from db.models import Base

# Default to SQLite for local dev, PostgreSQL for Docker
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./data/boter.db"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

async_session = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db():
    """Create all tables if they don't exist, then run column migrations."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # ── Column migrations (safe: IF NOT EXISTS) ──────────────────────────
        # Run after create_all so tables exist; skipped if columns already present.
        migrations = [
            # BotConfig new columns added after initial schema
            "ALTER TABLE bot_config ADD COLUMN IF NOT EXISTS ai_prompt_override TEXT",
            "ALTER TABLE bot_config ADD COLUMN IF NOT EXISTS ai_debug_channel_id BIGINT",
        ]
        for sql in migrations:
            try:
                await conn.execute(text(sql))
            except Exception as exc:
                # SQLite doesn't support IF NOT EXISTS on ALTER TABLE → skip
                import logging
                logging.getLogger("vex.db").debug(f"Migration skipped ({exc}): {sql}")


async def get_session() -> AsyncSession:
    """Get a new async session"""
    async with async_session() as session:
        return session


@asynccontextmanager
async def get_db():
    """Context manager for database sessions with auto-commit/rollback"""
    session = async_session()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
