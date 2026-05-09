"""WebSocket client for the WhatsApp Bridge add-on."""
from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

EventHandler = Callable[[dict[str, Any]], Awaitable[None]]
BACKOFF = (1, 2, 4, 8, 16, 30)


class WhatsAppWsClient:
    """Connects to /ws and dispatches events to a handler."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        token: str | None,
        handler: EventHandler,
    ) -> None:
        self._session = session
        self._host = host
        self._port = port
        self._token = token
        self._handler = handler
        self._task: asyncio.Task[None] | None = None
        self._stop = asyncio.Event()

    def update_token(self, token: str) -> None:
        self._token = token

    def start(self) -> None:
        if self._task is not None:
            return
        self._stop.clear()
        self._task = asyncio.create_task(self._run(), name="whatsapp_bridge_ws")

    async def stop(self) -> None:
        self._stop.set()
        task = self._task
        self._task = None
        if task is not None:
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):  # noqa: BLE001
                pass

    async def _run(self) -> None:
        attempt = 0
        url = f"http://{self._host}:{self._port}/ws"
        while not self._stop.is_set():
            try:
                headers = (
                    {"Authorization": f"Bearer {self._token}"}
                    if self._token
                    else {}
                )
                async with self._session.ws_connect(
                    url,
                    headers=headers,
                    timeout=15,
                    heartbeat=30,
                ) as ws:
                    attempt = 0
                    _LOGGER.debug("WhatsApp WS connected")
                    async for msg in ws:
                        if self._stop.is_set():
                            break
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                evt = json.loads(msg.data)
                            except ValueError:
                                _LOGGER.warning("Bad WS frame: %s", msg.data[:200])
                                continue
                            try:
                                await self._handler(evt)
                            except Exception:  # noqa: BLE001
                                _LOGGER.exception("WS handler raised")
                        elif msg.type in (
                            aiohttp.WSMsgType.CLOSED,
                            aiohttp.WSMsgType.CLOSE,
                            aiohttp.WSMsgType.ERROR,
                        ):
                            break
            except asyncio.CancelledError:
                raise
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("WS connection lost: %s", err)
            if self._stop.is_set():
                return
            delay = BACKOFF[min(attempt, len(BACKOFF) - 1)]
            attempt += 1
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=delay)
                return
            except asyncio.TimeoutError:
                continue
