"""
Short-term memory: Redis-backed session state.
Stores ephemeral conversation context that expires after inactivity.

Single-user mode: No tenant_id or user_id needed.
"""
import json

import structlog
from redis.asyncio import Redis

from src.config import settings

logger = structlog.get_logger()

SESSION_TTL_SECONDS = 7200  # 2 hours
DEFAULT_SESSION_KEY = "lifeos:session:default"


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

    def _session_key(self, session_id: str | None = None) -> str:
        if session_id:
            return f"lifeos:session:{session_id}"
        return DEFAULT_SESSION_KEY

    async def get_session(self, session_id: str | None = None) -> dict:
        """Get the current session state."""
        redis = await self._get_redis()
        key = self._session_key(session_id)
        data = await redis.get(key)
        if data is None:
            return {}
        return json.loads(data)

    async def set_session(self, state: dict, session_id: str | None = None) -> None:
        """Set the session state, resetting the TTL."""
        redis = await self._get_redis()
        key = self._session_key(session_id)
        await redis.set(key, json.dumps(state, default=str), ex=SESSION_TTL_SECONDS)

    async def update_session(self, updates: dict, session_id: str | None = None) -> dict:
        """Merge updates into the existing session state."""
        state = await self.get_session(session_id)
        state.update(updates)
        await self.set_session(state, session_id)
        return state

    async def clear_session(self, session_id: str | None = None) -> None:
        """Clear the session state."""
        redis = await self._get_redis()
        key = self._session_key(session_id)
        await redis.delete(key)

    async def add_to_message_history(
        self,
        role: str,
        content: str,
        max_messages: int = 20,
        session_id: str | None = None,
    ) -> None:
        """Append a message to the session's recent message history."""
        state = await self.get_session(session_id)
        history = state.get("message_history", [])
        history.append({"role": role, "content": content})
        if len(history) > max_messages:
            history = history[-max_messages:]
        state["message_history"] = history
        await self.set_session(state, session_id)

    async def get_message_history(self, session_id: str | None = None) -> list[dict]:
        """Get the recent message history from the session."""
        state = await self.get_session(session_id)
        return state.get("message_history", [])
