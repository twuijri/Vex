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
            "ALTER TABLE bot_config ADD COLUMN IF NOT EXISTS ai_alert_threshold FLOAT DEFAULT 0.5",
            "ALTER TABLE bot_config ADD COLUMN IF NOT EXISTS ai_auto_delete_threshold FLOAT DEFAULT 0.9",
            # AIProvider: base_url for self-hosted providers (LiteLLM)
            "ALTER TABLE ai_providers ADD COLUMN IF NOT EXISTS base_url VARCHAR(500)",
            # AIProvider: link to saved endpoint (connection profile)
            "ALTER TABLE ai_providers ADD COLUMN IF NOT EXISTS endpoint_id INTEGER REFERENCES ai_endpoints(id) ON DELETE CASCADE",
            # AIProviderStat: raw response column
            "ALTER TABLE ai_provider_stats ADD COLUMN IF NOT EXISTS last_raw_response TEXT",
        ]
        for sql in migrations:
            try:
                await conn.execute(text(sql))
            except Exception as exc:
                # SQLite doesn't support IF NOT EXISTS on ALTER TABLE → skip
                import logging
                logging.getLogger("vex.db").debug(f"Migration skipped ({exc}): {sql}")

    await _backfill_endpoints()


async def _backfill_endpoints():
    """Create an AIEndpoint for each legacy AIProvider row that has none,
    deduplicating by (provider_type, api_key, base_url)."""
    from db.models import AIProvider, AIEndpoint
    from sqlalchemy import select

    async with async_session() as session:
        result = await session.execute(
            select(AIProvider).where(AIProvider.endpoint_id.is_(None))
        )
        orphans = list(result.scalars().all())
        if not orphans:
            return

        ep_result = await session.execute(select(AIEndpoint))
        endpoints = list(ep_result.scalars().all())

        def find_endpoint(p):
            for ep in endpoints:
                if (ep.provider_type == p.provider_type
                        and ep.api_key == (p.api_key or "")
                        and (ep.base_url or None) == (p.base_url or None)):
                    return ep
            return None

        for p in orphans:
            ep = find_endpoint(p)
            if not ep:
                ep = AIEndpoint(
                    name=p.name,
                    provider_type=p.provider_type,
                    api_key=p.api_key or "",
                    base_url=p.base_url,
                )
                session.add(ep)
                await session.flush()
                endpoints.append(ep)
            p.endpoint_id = ep.id
        await session.commit()


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
