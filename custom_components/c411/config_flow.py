"""Config flow et options flow pour l'intégration C411."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .api import C411ApiClient, C411AuthError, C411ConnectionError
from .const import (
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)
from .coordinator import C411ConfigEntry

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def _validate_credentials(
    hass, username: str, password: str
) -> dict[str, Any]:
    """Valide les identifiants en effectuant un login + fetch.

    Retourne le bloc `user` en cas de succès. Lève C411AuthError /
    C411ConnectionError sinon.
    """
    session = async_get_clientsession(hass)
    client = C411ApiClient(session, username, password)
    await client.login()
    return await client.fetch_account()


class C411ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Gère le flux de configuration UI de C411."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Étape initiale : saisie et validation des identifiants."""
        errors: dict[str, str] = {}
        if user_input is not None:
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]
            try:
                user = await _validate_credentials(self.hass, username, password)
            except C411AuthError:
                errors["base"] = "invalid_auth"
            except C411ConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001 - garde-fou, structure du site changée
                _LOGGER.exception("Erreur inattendue pendant la validation C411")
                errors["base"] = "unknown"
            else:
                # Un compte = une entrée : on déduplique sur l'id utilisateur.
                await self.async_set_unique_id(str(user["id"]))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"C411 ({user.get('username', username)})",
                    data={CONF_USERNAME: username, CONF_PASSWORD: password},
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Déclenché par ConfigEntryAuthFailed : re-saisie des identifiants."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirme la ré-authentification."""
        errors: dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()
        if user_input is not None:
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]
            try:
                user = await _validate_credentials(self.hass, username, password)
            except C411AuthError:
                errors["base"] = "invalid_auth"
            except C411ConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Erreur inattendue pendant la ré-auth C411")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(str(user["id"]))
                self._abort_if_unique_id_mismatch(reason="wrong_account")
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data_updates={
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME,
                        default=reauth_entry.data.get(CONF_USERNAME),
                    ): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: C411ConfigEntry,
    ) -> C411OptionsFlow:
        """Retourne le gestionnaire d'options."""
        return C411OptionsFlow()


class C411OptionsFlow(OptionsFlow):
    """Options : intervalle de rafraîchissement."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure l'intervalle de scan."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        schema = vol.Schema(
            {
                vol.Required(CONF_SCAN_INTERVAL, default=current): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_SCAN_INTERVAL,
                        max=MAX_SCAN_INTERVAL,
                        step=1,
                        unit_of_measurement="s",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
