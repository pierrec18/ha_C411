"""Constantes pour l'intégration C411."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "c411"

# --- URLs de l'API c411.org -------------------------------------------------
BASE_URL: Final = "https://c411.org"
LOGIN_PAGE_URL: Final = f"{BASE_URL}/login"
AUTH_LOGIN_URL: Final = f"{BASE_URL}/api/auth/login"
AUTH_ME_URL: Final = f"{BASE_URL}/api/auth/me"

# Délai maximal (secondes) accordé à un appel HTTP individuel.
HTTP_TIMEOUT: Final = 30

# --- Coordinator ------------------------------------------------------------
CONF_SCAN_INTERVAL: Final = "scan_interval"
# Intervalle de rafraîchissement par défaut : 30 minutes.
DEFAULT_SCAN_INTERVAL: Final = 1800
MIN_SCAN_INTERVAL: Final = 60
MAX_SCAN_INTERVAL: Final = 86400
DEFAULT_UPDATE_INTERVAL: Final = timedelta(seconds=DEFAULT_SCAN_INTERVAL)

# --- Config entry -----------------------------------------------------------
CONF_USERNAME: Final = "username"
CONF_PASSWORD: Final = "password"

# Facteur de conversion octets -> GiB.
BYTES_PER_GIB: Final = 1024**3
