# FoodAI

Application de reconnaissance de plats avec interface web (auth Google + Supabase), historique et favoris.

## Structure
- `app/web/`: serveur FastAPI + interface web
- `app/ml/`: modèle de prédiction
- `app/core/`: recettes, unités, scaling
- `app/cli/`: commandes utilitaires
- `app/legacy/weeks/`: ancien code des semaines (archivé)

## Lancer l'application
```bash
pip install -r requirements.txt
python -m app.main --mode web
```

Interface: `http://localhost:8000`

## Variables d'environnement
Créer `.env` à la racine:
```env
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
```

## Tests
```bash
pytest -q
```
