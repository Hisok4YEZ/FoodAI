# Rapport des modifications FoodAI

Date de mise à jour: 2026-02-23
Projet: `AM1_projet`
Branche: `feature/leo`

## Objectif
Retirer totalement l'interface admin et les fonctions associées (ingestion candidats, retrain incrémental, endpoints admin) pour garder une application orientée usage final.

## Modifications réalisées

### 1) Backend FastAPI simplifié
Fichier: `AM1_projet/app/web/server.py`

- suppression des variables env admin:
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `ADMIN_TOKEN`
- suppression des helpers admin/retrain
- suppression des modèles Pydantic dédiés admin/retrain
- suppression de la route page admin:
  - `GET /admin`
- suppression des routes API admin:
  - `POST /api/admin/candidates/ingest`
  - `POST /api/admin/candidates/ingest/batch`
  - `GET /api/admin/candidates`
  - `PATCH /api/admin/candidates/{candidate_id}`
  - `POST /api/admin/retrain/incremental`
  - `GET /api/admin/retrain/status`

Le backend conserve uniquement les endpoints utiles à l'application utilisateur (auth, predict, profil, historique, favoris, dishes).

### 2) Suppression des fichiers frontend admin
Fichiers supprimés:
- `AM1_projet/app/web/templates/admin.html`
- `AM1_projet/app/web/static/js/admin.js`
- `AM1_projet/app/web/static/css/admin.css`

### 3) Suppression du script de retrain incrémental
Fichier supprimé:
- `AM1_projet/app/ml/retrain_incremental.py`

### 4) Documentation alignée
- `AM1_projet/README.md` réécrit pour refléter une app sans admin/retrain.
- chemins normalisés en mode projet (`AM1_projet/...`).

## Impact fonctionnel

### Conservé
- Login Google
- prédiction image + recette
- profil utilisateur
- historique
- favoris
- recalcul dynamique des portions côté frontend

### Retiré
- interface admin
- ingestion candidats
- retrain incrémental via API

## Vérification recommandée
1. Lancer le backend: `python -m app.main --mode web`
2. Vérifier que `/admin` n'existe plus.
3. Vérifier que les endpoints `/api/admin/...` retournent 404.
4. Tester le flux principal utilisateur: login, scan, favoris, historique, portions.
