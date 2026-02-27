"""
Vex - AI Provider CRUD Service
CRUD operations for managing AI providers via the web dashboard.
"""
import logging
from typing import Optional, List

from sqlalchemy import select

from db.database import get_db
from db.models import AIProvider

logger = logging.getLogger("vex.services.ai_provider")


async def list_providers() -> List[AIProvider]:
    """Return all providers ordered by priority (lowest first = first tried)."""
    async with get_db() as session:
        result = await session.execute(
            select(AIProvider).order_by(AIProvider.priority)
        )
        return list(result.scalars().all())


async def get_provider(provider_id: int) -> Optional[AIProvider]:
    """Get a single provider by ID."""
    async with get_db() as session:
        result = await session.execute(
            select(AIProvider).where(AIProvider.id == provider_id)
        )
        return result.scalar_one_or_none()


async def add_provider(
    name: str,
    provider_type: str,
    api_key: str,
    model: str,
    priority: int = 10,
) -> AIProvider:
    """Add a new AI provider."""
    async with get_db() as session:
        provider = AIProvider(
            name=name,
            provider_type=provider_type,
            api_key=api_key,
            model=model,
            priority=priority,
            is_active=True,
        )
        session.add(provider)
        await session.flush()
        await session.refresh(provider)
        return provider


async def delete_provider(provider_id: int) -> bool:
    """Delete a provider by ID. Returns True if deleted."""
    async with get_db() as session:
        result = await session.execute(
            select(AIProvider).where(AIProvider.id == provider_id)
        )
        provider = result.scalar_one_or_none()
        if provider:
            await session.delete(provider)
            return True
        return False


async def toggle_provider(provider_id: int) -> Optional[bool]:
    """Toggle active/inactive. Returns new state or None if not found."""
    async with get_db() as session:
        result = await session.execute(
            select(AIProvider).where(AIProvider.id == provider_id)
        )
        provider = result.scalar_one_or_none()
        if provider:
            provider.is_active = not provider.is_active
            return provider.is_active
        return None


async def move_provider(provider_id: int, direction: str) -> bool:
    """Move a provider up or down in priority order."""
    async with get_db() as session:
        all_result = await session.execute(
            select(AIProvider).order_by(AIProvider.priority)
        )
        providers = list(all_result.scalars().all())

        idx = next((i for i, p in enumerate(providers) if p.id == provider_id), None)
        if idx is None:
            return False

        if direction == "up" and idx > 0:
            swap_idx = idx - 1
        elif direction == "down" and idx < len(providers) - 1:
            swap_idx = idx + 1
        else:
            return False

        # Swap priorities
        providers[idx].priority, providers[swap_idx].priority = (
            providers[swap_idx].priority,
            providers[idx].priority,
        )
        return True
