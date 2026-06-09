<p align="center">
  <img src="images/logo-md.png" alt="C411" width="240">
</p>

# C411 — intégration Home Assistant

Intégration **custom** pour Home Assistant qui suit l'état de votre compte sur le
tracker BitTorrent privé [c411.org](https://c411.org) : ratio, volumes envoyés /
téléchargés, crédit d'upload, réputation, avertissements, statut freeleech, etc.

> ⚠️ **c411.org est un tracker privé, sur invitation.** Cette intégration ne fait
> qu'interroger l'API publique d'authentification du site avec **vos propres
> identifiants**. Elle ne contourne aucune protection et ne télécharge aucun
> contenu. Utilisez-la uniquement avec votre propre compte.

## Fonctionnement

L'intégration s'authentifie via le flux CSRF "double submit" du site
(GET `/login` → POST `/api/auth/login` → GET `/api/auth/me`) au sein d'une session
aiohttp partagée, puis rafraîchit périodiquement les statistiques du compte.
La ré-authentification est automatique lorsque la session expire.

- `iot_class` : `cloud_polling`
- Rafraîchissement par défaut : **30 minutes** (configurable de 60 s à 24 h).
- Aucune donnée sensible n'est journalisée (ni mot de passe, ni cookies de session).

## Installation via HACS (custom repository)

1. Dans Home Assistant, ouvrez **HACS**.
2. Menu **⋮** (en haut à droite) → **Custom repositories**.
3. Ajoutez l'URL du dépôt :
   `https://github.com/pierrec18/ha_C411`
   et choisissez la catégorie **Integration**.
4. Recherchez **C411** dans HACS, installez-la.
5. **Redémarrez** Home Assistant.

### Installation manuelle (alternative)

Copiez le dossier `custom_components/c411/` dans le répertoire
`config/custom_components/` de votre installation, puis redémarrez Home Assistant.

## Configuration

1. **Paramètres → Appareils et services → Ajouter une intégration**.
2. Cherchez **C411**.
3. Saisissez votre **nom d'utilisateur** et votre **mot de passe** c411.org.
   Les identifiants sont validés immédiatement (un login de test est effectué) et
   stockés chiffrés dans la config entry de Home Assistant. Aucun YAML ni
   `secrets.yaml` n'est nécessaire.

### Options

Une fois l'intégration ajoutée, **Configurer** permet de régler l'**intervalle de
rafraîchissement** (en secondes, défaut 1800).

## Entités exposées

Toutes les entités sont regroupées dans un seul appareil **C411 (votre pseudo)**.

### Capteurs (`sensor`)

| Entité          | Description                                  | Unité |
|-----------------|----------------------------------------------|-------|
| Ratio           | Ratio du compte (arrondi à 3 décimales)      | —     |
| Uploaded        | Volume total envoyé                          | GiB   |
| Downloaded      | Volume total téléchargé                      | GiB   |
| Upload credit   | Crédit d'upload                              | GiB   |
| Reputation      | Réputation                                   | —     |
| Warnings        | Nombre d'avertissements                      | —     |
| Minimum ratio   | Ratio minimum requis (diagnostic)            | —     |

Les capteurs de volume exposent aussi la valeur brute en octets dans leurs
attributs (`uploaded_bytes`, `downloaded_bytes`, `uploadCredit_bytes`).

### Capteurs binaires (`binary_sensor`)

| Entité        | Description                          |
|---------------|--------------------------------------|
| Can download  | Le téléchargement est-il autorisé    |
| Freeleech     | Freeleech actif                      |
| Donor         | Statut donateur (diagnostic)         |
| Warned        | Compte averti (`problem`)            |

## Développement / test du client API

Le client API est isolé de Home Assistant et testable seul :

```bash
C411_USER="VotrePseudo" C411_PASS="VotreMotDePasse" \
    python tests/manual_api_check.py
```

Le mot de passe provient uniquement de l'environnement, jamais codé en dur.

## Avertissement

Projet non officiel, sans aucun lien avec c411.org. Fourni « tel quel », sans
garantie. Respectez les règles du tracker.
