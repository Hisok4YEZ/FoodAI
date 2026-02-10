# Rapport des modifications FoodAI

Date: 2026-02-09

## 1) Correctifs authentification Google / Supabase
- Injection des variables Supabase depuis le backend vers le HTML (suppression de clé tronquée en dur).
- Gestion robuste du callback OAuth:
  - échange `code -> session` avec `exchangeCodeForSession`
  - fallback hash (`access_token`, `refresh_token`) avec `setSession`
- Stabilisation de la mise à jour UI après login/logout.
- Nettoyage de l'URL après callback OAuth.

Fichiers concernés:
- `app/web/server.py` (anciennement `app/week6/gui.py`)
- `app/web/web_interface.html` (anciennement `app/week6/web_interface.html`)

## 2) Zone utilisateur et préférences
- Ajout d'une zone utilisateur en haut à droite.
- Ajout d'un menu utilisateur:
  - Préférences
  - Historique
  - Favoris
  - Déconnexion
- Ajout d'une modal Préférences (prénom, nom, email, restrictions alimentaires).
- Connexion des actions UI aux endpoints backend du profil.

Fichier concerné:
- `app/web/web_interface.html`

## 3) Historique des scans
- Ajout d'une modal Historique avec:
  - chargement des scans
  - affichage date/confiance/portions
  - action "Voir"
  - action "Supprimer"
- Ajout du header `Authorization` côté frontend pour les appels authentifiés.

Backend:
- `GET /api/user/history`
- `DELETE /api/user/history/{scan_id}`

Fichiers concernés:
- `app/web/server.py`
- `app/web/web_interface.html`

## 4) Correctif RLS Supabase (cause historique vide)
- Le backend crée maintenant un client Supabase "scopé utilisateur" avec le JWT (`postgrest.auth(token)`).
- Les opérations profil/historique utilisent ce client utilisateur pour respecter les policies RLS.

Fichier concerné:
- `app/web/server.py`

## 5) Favoris (feature complète)
- Backend:
  - `GET /api/user/favorites`
  - `POST /api/user/favorites`
  - `DELETE /api/user/favorites/{favorite_id}`
- Frontend:
  - bouton "Ajouter aux favoris"
  - modal Favoris
  - actions "Voir" / "Supprimer"
- Payload favori inclut `recipe_payload` pour restaurer un résultat sans rescanner.

Fichiers concernés:
- `app/web/server.py`
- `app/web/web_interface.html`

## 6) Restructuration du projet
- Nouvelle organisation:
  - `app/web/` pour l'application web
  - `app/ml/` pour le predictor
  - `app/legacy/weeks/` pour l'ancien code semaine (archivé)
- Déplacement:
  - `app/week6/gui.py` -> `app/web/server.py`
  - `app/week6/web_interface.html` -> `app/web/web_interface.html`
  - `app/week5/predictor.py` -> `app/ml/predictor.py`
- Ajout de points d'entrée:
  - `app/main.py`
  - `app/__main__.py`

## 7) Nettoyage fichiers non essentiels
- Suppression de documents et fichiers parasites (PDF/doc temporaires, `.DS_Store`, caches python).
- Mise à jour du `README.md` avec la nouvelle structure et commande de lancement.

Commande de lancement actuelle:
- `python -m app.main --mode web`

