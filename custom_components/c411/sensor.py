"""Capteurs (sensors) pour l'intégration C411."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, UnitOfInformation
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import BYTES_PER_GIB
from .coordinator import C411ConfigEntry, C411Coordinator
from .entity import C411Entity


@dataclass(frozen=True, kw_only=True)
class C411SensorEntityDescription(SensorEntityDescription):
    """Décrit un capteur C411."""

    value_fn: Callable[[dict[str, Any]], Any]
    # Attributs supplémentaires (ex. valeur brute en octets).
    attr_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


def _to_gib(value: Any) -> float | None:
    """Convertit des octets en GiB, arrondi à 2 décimales."""
    if value is None:
        return None
    return round(value / BYTES_PER_GIB, 2)


def _bytes_attr(key: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Fabrique un attr_fn exposant la valeur brute en octets."""

    def _attrs(user: dict[str, Any]) -> dict[str, Any]:
        return {f"{key}_bytes": user.get(key)}

    return _attrs


SENSORS: tuple[C411SensorEntityDescription, ...] = (
    C411SensorEntityDescription(
        key="ratio",
        translation_key="ratio",
        icon="mdi:scale-balance",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        value_fn=lambda user: (
            None if user.get("ratio") is None else round(user["ratio"], 3)
        ),
    ),
    C411SensorEntityDescription(
        key="uploaded",
        translation_key="uploaded",
        icon="mdi:upload",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=2,
        value_fn=lambda user: _to_gib(user.get("uploaded")),
        attr_fn=_bytes_attr("uploaded"),
    ),
    C411SensorEntityDescription(
        key="downloaded",
        translation_key="downloaded",
        icon="mdi:download",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=2,
        value_fn=lambda user: _to_gib(user.get("downloaded")),
        attr_fn=_bytes_attr("downloaded"),
    ),
    C411SensorEntityDescription(
        key="upload_credit",
        translation_key="upload_credit",
        icon="mdi:gift",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda user: _to_gib(user.get("uploadCredit")),
        attr_fn=_bytes_attr("uploadCredit"),
    ),
    C411SensorEntityDescription(
        key="reputation",
        translation_key="reputation",
        icon="mdi:star",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda user: user.get("reputation"),
    ),
    C411SensorEntityDescription(
        key="warnings",
        translation_key="warnings",
        icon="mdi:alert",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda user: user.get("warnings"),
    ),
    C411SensorEntityDescription(
        key="min_ratio",
        translation_key="min_ratio",
        icon="mdi:scale-balance",
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=2,
        value_fn=lambda user: user.get("minRatioForDownload"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: C411ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Crée les capteurs C411."""
    coordinator = entry.runtime_data
    async_add_entities(
        C411Sensor(coordinator, description) for description in SENSORS
    )


class C411Sensor(C411Entity, SensorEntity):
    """Capteur C411 générique piloté par sa description."""

    entity_description: C411SensorEntityDescription

    @property
    def native_value(self) -> Any:
        """Valeur courante du capteur."""
        return self.entity_description.value_fn(self._user)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Attributs additionnels (valeurs brutes en octets)."""
        if self.entity_description.attr_fn is None:
            return None
        return self.entity_description.attr_fn(self._user)
