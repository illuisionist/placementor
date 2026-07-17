"""
Short-term memory using Redis.

Stores per-session conversation context, active tasks,
and current interview state. TTL-based auto-expiry.
"""

import json
from typing import Any, Optional

import redis.asyncio as aioredis
from config import settings


class ShortTermMemory:
    """Redis-backed session memory for a single student session."""

    def __init__(self):
        self._client: Optional[aioredis.Redis] = None

    async def get_client(self) -> aioredis.Redis:
        if self._client is None:
            self._client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
            )
        return self._client

    def _key(self, user_id: str, namespace: str) -> str:
        return f"placementor:{user_id}:{namespace}"

    # ── Conversation History ───────────────────────────────────────────

    async def append_message(self, user_id: str, role: str, content: str) -> None:
        """Append a chat message to conversation history."""
        client = await self.get_client()
        key = self._key(user_id, "chat_history")
        message = json.dumps({"role": role, "content": content})
        await client.rpush(key, message)
        await client.expire(key, settings.REDIS_SESSION_TTL)

    async def get_chat_history(self, user_id: str, last_n: int = 20) -> list[dict]:
        """Return last N messages from conversation history."""
        client = await self.get_client()
        key = self._key(user_id, "chat_history")
        raw = await client.lrange(key, -last_n, -1)
        return [json.loads(m) for m in raw]

    async def clear_chat_history(self, user_id: str) -> None:
        client = await self.get_client()
        await client.delete(self._key(user_id, "chat_history"))

    # ── Active Task State ─────────────────────────────────────────────

    async def set_active_task(self, user_id: str, task_data: dict) -> None:
        """Store the current active agent task."""
        client = await self.get_client()
        key = self._key(user_id, "active_task")
        await client.set(key, json.dumps(task_data), ex=settings.REDIS_SESSION_TTL)

    async def get_active_task(self, user_id: str) -> Optional[dict]:
        client = await self.get_client()
        key = self._key(user_id, "active_task")
        raw = await client.get(key)
        return json.loads(raw) if raw else None

    async def clear_active_task(self, user_id: str) -> None:
        client = await self.get_client()
        await client.delete(self._key(user_id, "active_task"))

    # ── Interview State ────────────────────────────────────────────────

    async def set_interview_state(self, user_id: str, state: dict) -> None:
        """Store current mock interview state."""
        client = await self.get_client()
        key = self._key(user_id, "interview_state")
        await client.set(key, json.dumps(state), ex=settings.REDIS_SESSION_TTL)

    async def get_interview_state(self, user_id: str) -> Optional[dict]:
        client = await self.get_client()
        key = self._key(user_id, "interview_state")
        raw = await client.get(key)
        return json.loads(raw) if raw else None

    async def clear_interview_state(self, user_id: str) -> None:
        client = await self.get_client()
        await client.delete(self._key(user_id, "interview_state"))

    # ── Generic KV Store ──────────────────────────────────────────────

    async def set(self, user_id: str, key: str, value: Any, ttl: Optional[int] = None) -> None:
        client = await self.get_client()
        full_key = self._key(user_id, key)
        await client.set(full_key, json.dumps(value), ex=ttl or settings.REDIS_SESSION_TTL)

    async def get(self, user_id: str, key: str) -> Optional[Any]:
        client = await self.get_client()
        raw = await client.get(self._key(user_id, key))
        return json.loads(raw) if raw else None

    async def delete(self, user_id: str, key: str) -> None:
        client = await self.get_client()
        await client.delete(self._key(user_id, key))

    async def close(self):
        if self._client:
            await self._client.aclose()


# Singleton instance
short_term_memory = ShortTermMemory()
