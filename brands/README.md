# Assets pour home-assistant/brands

Home Assistant ne lit pas le logo depuis ce dépôt d'intégration : pour que
l'icône s'affiche dans l'UI (page Intégrations, appareil), il faut soumettre ces
fichiers au dépôt officiel [home-assistant/brands](https://github.com/home-assistant/brands).

## Fichiers générés (domaine `c411`)

| Fichier        | Dimensions | Rôle                         |
|----------------|-----------:|------------------------------|
| `icon.png`     |    256×256 | Icône carrée                 |
| `icon@2x.png`  |    512×512 | Icône carrée haute résolution|
| `logo.png`     |    256×101 | Logo (plus grand côté 256)   |
| `logo@2x.png`  |    512×202 | Logo haute résolution        |

Tous en PNG RGBA, fond transparent.

## Procédure

1. Forkez `home-assistant/brands`.
2. Copiez le contenu de `custom_integrations/c411/` (ce dossier) au même chemin
   dans le fork : `custom_integrations/c411/`.
3. Ouvrez une pull request. La CI du dépôt valide dimensions, format et transparence.

> Astuce : l'icône carrée actuelle « letterboxe » le logo large. Si vous préférez
> une marque carrée plus pleine, remplacez `icon.png` / `icon@2x.png` par une
> version recadrée (par ex. uniquement le « C »).
