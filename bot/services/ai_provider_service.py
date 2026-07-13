"""
Vex - AI Provider CRUD Service
CRUD operations for managing AI endpoints (saved connections) and
AI models (cascade entries) via the web dashboard.
"""
import logging
from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from db.database import get_db
from db.models import AIProvider, AIEndpoint

logger = logging.getLogger("vex.services.ai_provider")


# ─── Endpoints (saved connections: base_url + key) ────────────────────────────

async def list_endpoints() -> List[dict]:
    """Return all saved endpoints with their linked-model counts."""
    async with get_db() as session:
        result = await session.execute(
            select(AIEndpoint, func.count(AIProvider.id))
            .outerjoin(AIProvider, AIProvider.endpoint_id == AIEndpoint.id)
            .group_by(AIEndpoint.id)
            .order_by(AIEndpoint.created_at)
        )
        return [
            {"endpoint": ep, "model_count": count}
            for ep, count in result.all()
        ]


async def get_endpoint(endpoint_id: int) -> Optional[AIEndpoint]:
    async with get_db() as session:
        result = await session.execute(
            select(AIEndpoint).where(AIEndpoint.id == endpoint_id)
        )
        return result.scalar_one_or_none()


async def add_endpoint(
    name: str,
    provider_type: str,
    api_key: str = "",
    base_url: str | None = None,
) -> AIEndpoint:
    async with get_db() as session:
        endpoint = AIEndpoint(
            name=name,
            provider_type=provider_type,
            api_key=api_key or "",
            base_url=base_url or None,
        )
        session.add(endpoint)
        await session.flush()
        await session.refresh(endpoint)
        return endpoint


async def update_endpoint(
    endpoint_id: int,
    name: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> bool:
    """Update endpoint fields (only non-None args are applied)."""
    async with get_db() as session:
        result = await session.execute(
            select(AIEndpoint).where(AIEndpoint.id == endpoint_id)
        )
        endpoint = result.scalar_one_or_none()
        if not endpoint:
            return False
        if name is not None and name.strip():
            endpoint.name = name.strip()
        if api_key is not None:
            endpoint.api_key = api_key
        if base_url is not None:
            endpoint.base_url = base_url.strip() or None
        return True


async def delete_endpoint(endpoint_id: int) -> bool:
    """Delete an endpoint (its linked models are cascade-deleted)."""
    async with get_db() as session:
        result = await session.execute(
            select(AIEndpoint).where(AIEndpoint.id == endpoint_id)
        )
        endpoint = result.scalar_one_or_none()
        if endpoint:
            await session.delete(endpoint)
            return True
        return False


# ─── Models (cascade entries) ─────────────────────────────────────────────────

async def list_providers() -> List[AIProvider]:
    """Return all providers ordered by priority (lowest first = first tried)."""
    async with get_db() as session:
        result = await session.execute(
            select(AIProvider)
            .options(selectinload(AIProvider.endpoint))
            .order_by(AIProvider.priority)
        )
        return list(result.scalars().all())


async def get_provider(provider_id: int) -> Optional[AIProvider]:
    """Get a single provider by ID."""
    async with get_db() as session:
        result = await session.execute(
            select(AIProvider)
            .options(selectinload(AIProvider.endpoint))
            .where(AIProvider.id == provider_id)
        )
        return result.scalar_one_or_none()


async def add_provider(
    name: str,
    endpoint_id: int,
    model: str,
    priority: int = 10,
) -> Optional[AIProvider]:
    """Add a new AI model entry linked to a saved endpoint."""
    async with get_db() as session:
        result = await session.execute(
            select(AIEndpoint).where(AIEndpoint.id == endpoint_id)
        )
        endpoint = result.scalar_one_or_none()
        if not endpoint:
            return None
        provider = AIProvider(
            name=name or model,
            provider_type=endpoint.provider_type,
            api_key=endpoint.api_key,
            model=model,
            priority=priority,
            is_active=True,
            base_url=endpoint.base_url,
            endpoint_id=endpoint.id,
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


async def reorder_providers(ordered_ids: List[int]) -> bool:
    """Set cascade priorities from an explicitly ordered list of provider ids
    (drag-and-drop). Ids not in the list keep their relative order after it."""
    async with get_db() as session:
        result = await session.execute(
            select(AIProvider).order_by(AIProvider.priority, AIProvider.id)
        )
        providers = {p.id: p for p in result.scalars().all()}
        rank = 1
        for pid in ordered_ids:
            if pid in providers:
                providers[pid].priority = rank
                providers.pop(pid)
                rank += 1
        for p in providers.values():  # leftovers keep relative order at the end
            p.priority = rank
            rank += 1
        return True


async def move_provider(provider_id: int, direction: str) -> bool:
    """Move a provider up or down in priority order."""
    async with get_db() as session:
        all_result = await session.execute(
            select(AIProvider).order_by(AIProvider.priority, AIProvider.id)
        )
        providers = list(all_result.scalars().all())

        # Normalize priorities to 1, 2, 3, ... so swapping always changes values
        for i, p in enumerate(providers):
            p.priority = i + 1
        await session.flush()

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
