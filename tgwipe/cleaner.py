import asyncio
import time
from typing import Self

from loguru import logger
from telethon import TelegramClient, errors
from telethon.tl.custom.message import Message
from telethon.types import Channel, Chat, User

BATCH_SIZE = 100
GroupEntity = Channel | Chat | User


class Cleaner:
    def __init__(self, api_id: int, api_hash: str, session: str) -> None:
        self.client = TelegramClient(session, api_id, api_hash)

    async def __aenter__(self) -> Self:
        await self.client.start()
        me = await self.client.get_me()
        logger.info("Logged in as {} (@{})", me.first_name, me.username or me.id)
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.client.disconnect()

    async def resolve_group(self, group_input: str) -> GroupEntity:
        target: str | int
        try:
            target = int(group_input)
        except ValueError:
            target = group_input
        group = await self.client.get_entity(target)
        logger.info("Resolved group: {}", getattr(group, "title", group.id))
        return group

    async def collect_my_messages(self, group: GroupEntity) -> list[Message]:
        logger.info("Scanning your messages")
        messages: list[Message] = []
        async for msg in self.client.iter_messages(group, from_user="me", wait_time=1):
            messages.append(msg)
            if len(messages) % 500 == 0:
                logger.debug("Found {:,} so far", len(messages))
        logger.info("Found {:,} messages", len(messages))
        return messages

    async def delete_messages(self, group: GroupEntity, msg_ids: list[int]) -> int:
        deleted = 0
        total = len(msg_ids)
        start = time.monotonic()

        for i in range(0, total, BATCH_SIZE):
            batch = msg_ids[i : i + BATCH_SIZE]
            try:
                await self.client.delete_messages(group, batch, revoke=True)
                deleted += len(batch)
            except errors.FloodWaitError as e:
                logger.warning("Rate-limited; waiting {}s", e.seconds)
                await asyncio.sleep(e.seconds + 2)
                await self.client.delete_messages(group, batch, revoke=True)
                deleted += len(batch)
            except errors.RPCError as e:
                logger.error("Error on batch at index {}: {}; skipping", i, e)
                continue

            pct = deleted / total * 100
            elapsed = time.monotonic() - start
            logger.info(
                "Deleted {:,}/{:,} ({:.0f}%) in {:.0f}s",
                deleted,
                total,
                pct,
                elapsed,
            )

        logger.success(
            "Deleted {:,} messages in {:.1f}s",
            deleted,
            time.monotonic() - start,
        )
        return deleted
