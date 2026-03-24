"""
Short-term memory: Redis-backed session state.
Stores ephemeral conversation context that expires after inactivity.
"""
import json
import uuid

import structlog
from redis.asyncio import Redis

from src.config import settings

logger = structlog.get_logger()

SESSION_TTL_SECONDS = 7200  # 2 hours


class ShortTermMemory:
    """
    Redis-backed short-term memory for conversation sessions.
    Stores: active workflow state, recent message history, session metadata.
    """

    def __init__(self, redis: Redis | None = None) -> None:
        self._redis = redis

    async def _get_redis(self) -> Redis:
        if self._redis is None:
            self._redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    def _session_key(self, tenant_id: uuid.UUID, user_id: uuid.UUID) -> str:
        return f"{tenant_id}:session:{user_id}"

    async def get_session(
        self, tenant_id: uuid.UUID, user_id: uuid.UUID
    ) -> dict:
        """Get the current session state for a user."""
        redis = await self._get_redis()
        key = self._session_key(tenant_id, user_id)
        data = await redis.get(key)
        if data is None:
            return {}
        return json.loads(data)

    async def set_session(
        self, tenant_id: uuid.UUID, user_id: uuid.UUID, state: dict
    ) -> None:
        """Set the session state, resetting the TTL."""
        redis = await self._get_redis()
        key = self._session_key(tenant_id, user_id)
        await redis.set(key, json.dumps(state, default=str), ex=SESSION_TTL_SECONDS)

    async def update_session(
        self, tenant_id: uuid.UUID, user_id: uuid.UUID, updates: dict
    ) -> dict:
        """Merge updates into the existing session state."""
        state = await self.get_session(tenant_id, user_id)
        state.update(updates)
        await self.set_session(tenant_id, user_id, state)
        return state

    async def clear_session(
        self, tenant_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        """Clear the session state."""
        redis = await self._get_redis()
        key = self._session_key(tenant_id, user_id)
        await redis.delete(key)

    async def add_to_message_history(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        content: str,
        max_messages: int = 20,
    ) -> None:
        """Append a message to the session's recent message history."""
        state = await self.get_session(tenant_id, user_id)
        history = state.get("message_history", [])
        history.append({"role": role, "content": content})
        if len(history) > max_messages:
            history = history[-max_messages:]
        state["message_history"] = history
        await self.set_session(tenant_id, user_id, state)

    async def get_message_history(
        self, tenant_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[dict]:
        """Get the recent message history from the session."""
        state = await self.get_session(tenant_id, user_id)
        return state.get("message_history", [])
