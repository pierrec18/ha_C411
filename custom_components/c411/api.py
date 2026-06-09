"""Client API pour le tracker privé c411.org.

Ce module est volontairement indépendant de Home Assistant : il ne contient
que la logique de transport et d'authentification, ce qui le rend réutilisable
et testable de façon isolée (voir tests/manual_api_check.py).

Flux d'authentification (protection CSRF "double submit") :
  1. GET /login          -> dépose le cookie `__csrf` ET expose le token CSRF
                            dans une balise <meta name="csrf-token" content="...">.
                            Le cookie et la meta DOIVENT provenir du même GET.
  2. POST /api/auth/login -> header `csrf-token` (meta) + cookie `__csrf` renvoyé
                            automatiquement par la session ; dépose le cookie de
                            session `__Host-c411_session`.
  3. GET /api/auth/me    -> renvoie le JSON complet du compte.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

import aiohttp

from .const import (
    AUTH_LOGIN_URL,
    AUTH_ME_URL,
    HTTP_TIMEOUT,
    LOGIN_PAGE_URL,
)

_LOGGER = logging.getLogger(__name__)

# Extraction défensive du token CSRF dans le HTML Nuxt. On gère les deux ordres
# d'attributs possibles (name avant content, ou l'inverse) et les guillemets
# simples ou doubles. Si rien ne matche, c'est probablement que la structure du
# site a changé : on lève alors une erreur explicite.
_CSRF_META_PATTERNS = (
    re.compile(
        r'<meta[^>]*name=["\']csrf-token["\'][^>]*content=["\']([^"\']+)["\']',
        re.IGNORECASE,
    ),
    re.compile(
        r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*name=["\']csrf-token["\']',
        re.IGNORECASE,
    ),
)

_TIMEOUT = aiohttp.ClientTimeout(total=HTTP_TIMEOUT)


class C411Error(Exception):
    """Erreur générique du client C411."""


class C411AuthError(C411Error):
    """Identifiants invalides ou session impossible à établir.

    À mapper vers ConfigEntryAuthFailed côté Home Assistant.
    """


class C411ConnectionError(C411Error):
    """Erreur réseau/HTTP transitoire.

    À mapper vers UpdateFailed côté Home Assistant.
    """


class _CsrfError(C411Error):
    """Erreur CSRF interne (cookie absent / token périmé) -> on retente le flux."""


def _extract_csrf_token(html: str) -> str:
    """Extrait le token CSRF de la balise meta ; lève si introuvable."""
    for pattern in _CSRF_META_PATTERNS:
        if match := pattern.search(html):
            return match.group(1)
    raise C411Error(
        "Token CSRF introuvable dans la page de login "
        "(la structure du site a peut-être changé)"
    )


async def _safe_json(response: aiohttp.ClientResponse) -> dict[str, Any]:
    """Décode le JSON d'une réponse en tolérant un content-type incorrect."""
    try:
        data = await response.json(content_type=None)
    except (aiohttp.ContentTypeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


class C411ApiClient:
    """Client authentifié vers l'API c411.org."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        username: str,
        password: str,
    ) -> None:
        """Initialise le client.

        La `session` (avec son cookie jar) est partagée entre tous les appels :
        c'est elle qui conserve `__csrf` puis `__Host-c411_session`.
        """
        self._session = session
        self._username = username
        self._password = password

    async def _get_csrf(self) -> str:
        """Étape 1 : récupère le token CSRF (et dépose le cookie `__csrf`)."""
        try:
            async with self._session.get(
                LOGIN_PAGE_URL, timeout=_TIMEOUT
            ) as response:
                response.raise_for_status()
                html = await response.text()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise C411ConnectionError(
                f"Échec de récupération de la page de login : {err}"
            ) from err
        return _extract_csrf_token(html)

    async def _post_login(self, csrf_token: str) -> None:
        """Étape 2 : poste les identifiants avec le token CSRF.

        Le cookie `__csrf` est renvoyé automatiquement par la session.
        """
        payload = {"username": self._username, "password": self._password}
        headers = {"content-type": "application/json", "csrf-token": csrf_token}
        try:
            async with self._session.post(
                AUTH_LOGIN_URL, json=payload, headers=headers, timeout=_TIMEOUT
            ) as response:
                data = await _safe_json(response)
                if response.status == 401:
                    # Identifiants faux : on NE logge jamais le mot de passe.
                    _LOGGER.warning(
                        "Échec d'authentification C411 pour l'utilisateur %s "
                        "(identifiants invalides)",
                        self._username,
                    )
                    raise C411AuthError("Nom d'utilisateur ou mot de passe invalide")
                if response.status == 403:
                    # "CSRF Cookie not found" / "CSRF Token Mismatch" : non fatal,
                    # on relancera l'étape 1 pour obtenir un couple cookie/token frais.
                    _LOGGER.debug(
                        "Réponse CSRF 403 : %s",
                        data.get("message", "inconnu"),
                    )
                    raise _CsrfError(data.get("message", "CSRF error"))
                response.raise_for_status()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise C411ConnectionError(
                f"Échec de l'appel de login : {err}"
            ) from err

        if not data.get("success"):
            raise C411AuthError("Réponse de login inattendue (success absent)")

    async def login(self) -> None:
        """Exécute le flux d'authentification complet (étapes 1 → 2).

        Retente une fois en cas d'erreur CSRF (cookie/token désynchronisés).
        Lève C411AuthError si les identifiants sont invalides.
        """
        last_csrf_error: _CsrfError | None = None
        for attempt in range(2):
            csrf_token = await self._get_csrf()
            try:
                await self._post_login(csrf_token)
            except _CsrfError as err:
                last_csrf_error = err
                _LOGGER.debug("Tentative de login %d : erreur CSRF, on retente", attempt + 1)
                continue
            else:
                _LOGGER.debug("Authentification C411 réussie pour %s", self._username)
                return
        raise C411ConnectionError(
            f"Échec CSRF répété lors du login : {last_csrf_error}"
        )

    async def _get_me(self) -> dict[str, Any]:
        """Étape 3 : récupère le JSON du compte via les cookies de session."""
        try:
            async with self._session.get(AUTH_ME_URL, timeout=_TIMEOUT) as response:
                response.raise_for_status()
                return await _safe_json(response)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise C411ConnectionError(
                f"Échec de récupération du compte : {err}"
            ) from err

    async def fetch_account(self) -> dict[str, Any]:
        """Retourne le bloc `user` du compte, en ré-authentifiant si besoin.

        Si la session est absente/expirée (`authenticated` falsy), relance le
        flux d'auth complet puis réessaie une seule fois.
        """
        data = await self._get_me()
        if not data.get("authenticated"):
            _LOGGER.debug("Session C411 absente/expirée, ré-authentification")
            await self.login()
            data = await self._get_me()
            if not data.get("authenticated"):
                raise C411AuthError(
                    "Session toujours invalide après ré-authentification"
                )

        user = data.get("user")
        if not isinstance(user, dict):
            raise C411ConnectionError("Bloc 'user' absent de la réponse /me")
        return user
