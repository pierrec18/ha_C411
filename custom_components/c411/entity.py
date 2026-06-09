"""Entité de base partagée par les plateformes C411."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import C411Coordinator


class C411Entity(CoordinatorEntity[C411Coordinator]):
    """Base commune : rattache l'entité au device C411 unique."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: C411Coordinator,
        description: EntityDescription,
    ) -> None:
        """Initialise l'entité et son `unique_id` stable."""
        super().__init__(coordinator)
        self.entity_description = description

        # L'id utilisateur identifie de façon stable le device et les entités.
        user_id = coordinator.data["id"]
        username = coordinator.data.get("username", str(user_id))

        self._attr_unique_id = f"{user_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(user_id))},
            name=f"C411 ({username})",
            manufacturer="c411.org",
            model="Compte tracker",
            configuration_url="https://c411.org",
        )

    @property
    def _user(self) -> dict:
        """Raccourci vers le bloc `user` rafraîchi par le coordinator."""
        return self.coordinator.data
