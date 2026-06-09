"""DataUpdateCoordinator pour l'intégration C411."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import C411ApiClient, C411AuthError, C411ConnectionError
from .const import (
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

type C411ConfigEntry = ConfigEntry[C411Coordinator]


class C411Coordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordonne le rafraîchissement périodique du compte C411.

    Le client API gère lui-même la ré-authentification : si /api/auth/me
    indique une session expirée, il relance le flux complet puis réessaie.
    """

    config_entry: C411ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: C411ConfigEntry) -> None:
        """Initialise le coordinator depuis la config entry."""
        scan_interval = entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        session = async_get_clientsession(hass)
        self.client = C411ApiClient(
            session,
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Récupère les statistiques du compte."""
        try:
            return await self.client.fetch_account()
        except C411AuthError as err:
            # Identifiants invalides -> déclenche la reconfiguration HA.
            raise ConfigEntryAuthFailed(str(err)) from err
        except C411ConnectionError as err:
            # Erreur transitoire -> HA réessaiera au prochain cycle.
            raise UpdateFailed(str(err)) from err
