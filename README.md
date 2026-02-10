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
SUPABASE_SERVICE_ROLE_KEY=...
ADMIN_TOKEN=...
# optionnel
SUPABASE_IMAGE_BUCKET=scan-images
```

## Tests
```bash
pytest -q
```

## Retrain manuel du modele (complet)
```bash
python -m app.ml.retrain --data data/food --epochs 5 --batch-size 16
```

Le modele est ecrit dans `models/model_food.pth`.

## Retrain incremental (batch + replay)
Le retrain rapide utilise seulement les nouveaux candidats approuves + un echantillon des anciennes classes (replay) pour limiter l'oubli catastrophique.

Script:
```bash
python -m app.ml.retrain_incremental \
  --batch-dir data/auto_batches/<batch_id> \
  --base-model models/model_food.pth \
  --out models/model_food.pth \
  --data data/food \
  --epochs 2 \
  --replay-per-class 20
```

## Automatisation n8n + Admin
1. Exécuter le SQL:
- `docs/n8n/dish_candidates_schema.sql`

2. Ouvrir l'interface admin:
- `http://localhost:8000/admin`

3. Importer le workflow n8n:
- complet (2 agents + Openverse + batch): `docs/n8n/foodai_n8n_cloud_free_v4_batch_two_agents.json`
- `docs/n8n/foodai_n8n_cloud_free_v3_single_agent.json`

4. Endpoints admin utilises:
- `POST /api/admin/candidates/n8n` (ingestion candidats, `auto_approve` possible)
- `POST /api/admin/candidates/n8n/batch` (ingestion batch)
- `GET /api/admin/candidates`
- `PATCH /api/admin/candidates/{candidate_id}`
- `POST /api/admin/retrain/incremental`
- `GET /api/admin/retrain/status`

Si tu veux un retrain ultra rapide uniquement sur le batch, mets `replay_per_class=0`.
Attention: ce mode oublie plus facilement les anciennes classes.
