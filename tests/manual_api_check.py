"""Test manuel du client C411ApiClient, hors Home Assistant.

Usage :
    C411_USER="votre_pseudo" C411_PASS="votre_mot_de_passe" \
        python tests/manual_api_check.py

Le mot de passe n'est JAMAIS écrit en dur : il vient des variables
d'environnement. Le script affiche les statistiques principales du compte
sans jamais imprimer le mot de passe ni les cookies.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import aiohttp

# Permet d'importer le package `custom_components.c411` depuis la racine du repo.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from custom_components.c411.api import (  # noqa: E402
    C411ApiClient,
    C411AuthError,
    C411ConnectionError,
)


async def _main() -> int:
    username = os.environ.get("C411_USER")
    password = os.environ.get("C411_PASS")
    if not username or not password:
        print("Définis C411_USER et C411_PASS dans l'environnement.", file=sys.stderr)
        return 2

    async with aiohttp.ClientSession() as session:
        client = C411ApiClient(session, username, password)
        try:
            user = await client.fetch_account()
        except C411AuthError as err:
            print(f"[AUTH] Identifiants refusés : {err}", file=sys.stderr)
            return 1
        except C411ConnectionError as err:
            print(f"[RESEAU] {err}", file=sys.stderr)
            return 1

    print("Authentification OK. Compte :")
    print(f"  id           : {user.get('id')}")
    print(f"  username     : {user.get('username')}")
    print(f"  ratio        : {user.get('ratio')}")
    print(f"  uploaded     : {user.get('uploaded')} octets")
    print(f"  downloaded   : {user.get('downloaded')} octets")
    print(f"  uploadCredit : {user.get('uploadCredit')} octets")
    print(f"  canDownload  : {user.get('canDownload')}")
    print(f"  isFreeleech  : {user.get('isFreeleech')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
