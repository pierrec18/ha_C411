"""Intégration C411 (tracker privé c411.org)."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import C411ConfigEntry, C411Coordinator

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: C411ConfigEntry) -> bool:
    """Configure une entrée C411."""
    coordinator = C411Coordinator(hass, entry)
    # Premier refresh : valide l'auth et peuple les données avant les plateformes.
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Recharge l'entrée si les options (intervalle) changent.
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: C411ConfigEntry) -> bool:
    """Décharge une entrée C411."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(hass: HomeAssistant, entry: C411ConfigEntry) -> None:
    """Recharge l'entrée quand les options sont modifiées."""
    await hass.config_entries.async_reload(entry.entry_id)
