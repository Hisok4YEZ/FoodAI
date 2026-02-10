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

## Retrain manuel du modele
```bash
python -m app.ml.retrain --data data/food --epochs 5 --batch-size 16
```

Le modele est ecrit dans `models/model_food.pth`.

## Automatisation n8n + Admin
1. Ajouter dans `.env`:
```env
ADMIN_TOKEN=ton_token_admin
SUPABASE_SERVICE_ROLE_KEY=ta_service_role_key
# optionnel
SUPABASE_IMAGE_BUCKET=scan-images
```

2. Exécuter le SQL:
- `docs/n8n/dish_candidates_schema.sql`

3. Ouvrir l'interface admin:
- `http://localhost:8000/admin`

4. Importer le workflow n8n template:
- `docs/n8n/foodai_n8n_workflow_template.json`

Le workflow pousse les candidats vers:
- `POST /api/admin/candidates/n8n` avec header `X-Admin-Token`.

