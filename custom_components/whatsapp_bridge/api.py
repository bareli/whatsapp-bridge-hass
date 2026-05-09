"""HTTP client for the WhatsApp Bridge add-on."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=15)


class WhatsAppError(Exception):
    """Base error."""


class WhatsAppAuthError(WhatsAppError):
    """Auth failed."""


class WhatsAppOfflineError(WhatsAppError):
    """Bridge is unreachable or not ready."""


class WhatsAppRateLimitError(WhatsAppError):
    """Rate limited by the bridge."""


class WhatsAppApiClient:
    """Tiny REST client for the add-on."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        token: str | None,
    ) -> None:
        self._session = session
        self._host = host
        self._port = port
        self._token = token

    @property
    def base_url(self) -> str:
        return f"http://{self._host}:{self._port}"

    def update_token(self, token: str) -> None:
        self._token = token

    @property
    def token(self) -> str | None:
        return self._token

    def _headers(self, *, with_auth: bool = True) -> dict[str, str]:
        headers: dict[str, str] = {"Accept": "application/json"}
        if with_auth and self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def healthz(self) -> bool:
        try:
            async with self._session.get(
                f"{self.base_url}/healthz",
                timeout=DEFAULT_TIMEOUT,
            ) as resp:
                return resp.status == 200
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return False

    async def bootstrap_token(self) -> str | None:
        """Fetch the auto-generated token. One-shot; returns None after disabled."""
        try:
            async with self._session.get(
                f"{self.base_url}/bootstrap",
                headers=self._headers(with_auth=False),
                timeout=DEFAULT_TIMEOUT,
            ) as resp:
                if resp.status == 404:
                    return None
                resp.raise_for_status()
                data = await resp.json()
                return data.get("token")
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise WhatsAppOfflineError(str(err)) from err

    async def status(self) -> dict[str, Any]:
        return await self._get("/status")

    async def get_qr_png(self) -> bytes | None:
        try:
            async with self._session.get(
                f"{self.base_url}/qr.png",
                headers=self._headers(),
                timeout=DEFAULT_TIMEOUT,
            ) as resp:
                if resp.status == 404:
                    return None
                if resp.status == 401:
                    raise WhatsAppAuthError("invalid token")
                resp.raise_for_status()
                return await resp.read()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise WhatsAppOfflineError(str(err)) from err

    async def send_text(
        self, to: str, body: str, quoted_msg_id: str | None = None
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"to": to, "body": body}
        if quoted_msg_id:
            payload["quoted_msg_id"] = quoted_msg_id
        return await self._post_json("/send/text", payload)

    async def send_media(
        self,
        to: str,
        data: bytes,
        filename: str,
        content_type: str,
        *,
        caption: str | None = None,
        as_document: bool = False,
        as_voice: bool = False,
    ) -> dict[str, Any]:
        form = aiohttp.FormData()
        form.add_field("to", to)
        if caption:
            form.add_field("caption", caption)
        if as_document:
            form.add_field("as_document", "true")
        if as_voice:
            form.add_field("as_voice", "true")
        form.add_field(
            "file",
            data,
            filename=filename,
            content_type=content_type,
        )
        try:
            async with self._session.post(
                f"{self.base_url}/send/media",
                headers=self._headers(),
                data=form,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                if resp.status == 401:
                    raise WhatsAppAuthError("invalid token")
                if resp.status == 429:
                    raise WhatsAppRateLimitError("rate limited")
                if resp.status >= 500:
                    raise WhatsAppOfflineError(await resp.text())
                resp.raise_for_status()
                return await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise WhatsAppOfflineError(str(err)) from err

    async def send_location(
        self, to: str, lat: float, lng: float, name: str | None = None
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"to": to, "lat": lat, "lng": lng}
        if name:
            payload["name"] = name
        return await self._post_json("/send/location", payload)

    async def list_contacts(self) -> list[dict[str, Any]]:
        return await self._get("/contacts")

    async def session_logout(self) -> None:
        await self._post_json("/session/logout", {})

    async def session_restart(self) -> None:
        await self._post_json("/session/restart", {})

    async def _get(self, path: str) -> Any:
        try:
            async with self._session.get(
                f"{self.base_url}{path}",
                headers=self._headers(),
                timeout=DEFAULT_TIMEOUT,
            ) as resp:
                self._check_status(resp.status)
                resp.raise_for_status()
                return await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise WhatsAppOfflineError(str(err)) from err

    async def _post_json(self, path: str, payload: dict[str, Any]) -> Any:
        try:
            async with self._session.post(
                f"{self.base_url}{path}",
                headers={**self._headers(), "Content-Type": "application/json"},
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                self._check_status(resp.status)
                resp.raise_for_status()
                if resp.content_length == 0:
                    return {}
                return await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise WhatsAppOfflineError(str(err)) from err

    @staticmethod
    def _check_status(status: int) -> None:
        if status == 401:
            raise WhatsAppAuthError("invalid token")
        if status == 429:
            raise WhatsAppRateLimitError("rate limited")
        if status == 503:
            raise WhatsAppOfflineError("bridge not ready")
