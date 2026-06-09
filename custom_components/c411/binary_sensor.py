"""Capteurs binaires (binary sensors) pour l'intégration C411."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import C411ConfigEntry
from .entity import C411Entity


@dataclass(frozen=True, kw_only=True)
class C411BinarySensorEntityDescription(BinarySensorEntityDescription):
    """Décrit un capteur binaire C411."""

    value_fn: Callable[[dict[str, Any]], bool | None]


BINARY_SENSORS: tuple[C411BinarySensorEntityDescription, ...] = (
    C411BinarySensorEntityDescription(
        key="can_download",
        translation_key="can_download",
        icon="mdi:download-circle",
        value_fn=lambda user: user.get("canDownload"),
    ),
    C411BinarySensorEntityDescription(
        key="is_freeleech",
        translation_key="is_freeleech",
        icon="mdi:gift-open",
        value_fn=lambda user: user.get("isFreeleech"),
    ),
    C411BinarySensorEntityDescription(
        key="is_donor",
        translation_key="is_donor",
        icon="mdi:heart",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda user: user.get("isDonor"),
    ),
    C411BinarySensorEntityDescription(
        key="is_warned",
        translation_key="is_warned",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:alert-octagon",
        value_fn=lambda user: user.get("isWarned"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: C411ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Crée les capteurs binaires C411."""
    coordinator = entry.runtime_data
    async_add_entities(
        C411BinarySensor(coordinator, description)
        for description in BINARY_SENSORS
    )


class C411BinarySensor(C411Entity, BinarySensorEntity):
    """Capteur binaire C411 générique piloté par sa description."""

    entity_description: C411BinarySensorEntityDescription

    @property
    def is_on(self) -> bool | None:
        """État booléen courant."""
        value = self.entity_description.value_fn(self._user)
        return None if value is None else bool(value)
