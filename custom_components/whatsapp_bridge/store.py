"""Phonebook storage for WhatsApp Bridge."""
from __future__ import annotations

import asyncio
import re
import uuid
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION

_PHONE_RE = re.compile(r"^\+?[0-9]{6,20}$")


def _normalise_phone(phone: str) -> str:
    cleaned = re.sub(r"[^0-9+]", "", phone or "")
    if not _PHONE_RE.match(cleaned):
        raise ValueError("invalid_phone")
    if not cleaned.startswith("+"):
        cleaned = "+" + cleaned
    return cleaned


class PhonebookStore:
    """Wraps helpers.storage.Store for the contacts list."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._contacts: list[dict[str, Any]] = []
        self._loaded = False
        self._lock = asyncio.Lock()

    async def async_load(self) -> None:
        if self._loaded:
            return
        async with self._lock:
            if self._loaded:
                return
            data = await self._store.async_load()
            self._contacts = list((data or {}).get("contacts", []))
            self._loaded = True

    async def async_list(self) -> list[dict[str, Any]]:
        await self.async_load()
        return [dict(c) for c in self._contacts]

    async def async_create(
        self,
        name: str,
        phone: str,
        tags: list[str] | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        await self.async_load()
        async with self._lock:
            contact = {
                "id": uuid.uuid4().hex,
                "name": (name or "").strip()[:128] or "Unnamed",
                "phone": _normalise_phone(phone),
                "tags": [str(t)[:32] for t in (tags or [])][:16],
                "notes": (notes or "").strip()[:1024],
            }
            self._contacts.append(contact)
            await self._save()
            return dict(contact)

    async def async_update(
        self, contact_id: str, **changes: Any
    ) -> dict[str, Any]:
        await self.async_load()
        async with self._lock:
            for c in self._contacts:
                if c["id"] == contact_id:
                    if "name" in changes and changes["name"] is not None:
                        c["name"] = str(changes["name"]).strip()[:128] or "Unnamed"
                    if "phone" in changes and changes["phone"]:
                        c["phone"] = _normalise_phone(changes["phone"])
                    if "tags" in changes and changes["tags"] is not None:
                        c["tags"] = [str(t)[:32] for t in changes["tags"]][:16]
                    if "notes" in changes and changes["notes"] is not None:
                        c["notes"] = str(changes["notes"]).strip()[:1024]
                    await self._save()
                    return dict(c)
            raise KeyError(contact_id)

    async def async_delete(self, contact_id: str) -> None:
        await self.async_load()
        async with self._lock:
            before = len(self._contacts)
            self._contacts = [c for c in self._contacts if c["id"] != contact_id]
            if len(self._contacts) == before:
                raise KeyError(contact_id)
            await self._save()

    async def async_resolve(self, target: str) -> str:
        """Resolve a phone-or-id target to an E.164 phone."""
        await self.async_load()
        for c in self._contacts:
            if c["id"] == target or c["name"].casefold() == target.casefold():
                return c["phone"]
        return _normalise_phone(target)

    async def _save(self) -> None:
        await self._store.async_save({"contacts": self._contacts})
