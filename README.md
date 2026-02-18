# FoodAI

Application web de reconnaissance de plats avec:
- authentification Google (Supabase Auth)
- profil utilisateur (préférences + consentement image)
- historique des scans
- favoris
- interface admin (candidats n8n)
- scripts de retrain du modèle

## Structure
- `/Users/yunes/Documents/New project/AM1_projet/app/web/` : serveur FastAPI + frontend
- `/Users/yunes/Documents/New project/AM1_projet/app/ml/` : prédiction + retrain
- `/Users/yunes/Documents/New project/AM1_projet/app/core/` : recettes, unités, scaling
- `/Users/yunes/Documents/New project/AM1_projet/app/data/recipes.json` : base recettes
- `/Users/yunes/Documents/New project/AM1_projet/data/food/` : dataset d'entraînement
- `/Users/yunes/Documents/New project/AM1_projet/docs/n8n/` : workflows n8n

## Installation (recommandée)
Utilise Python 3.10 pour éviter les conflits de dépendances ML.

```bash
cd "/Users/yunes/Documents/New project/AM1_projet"
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Variables d'environnement
Créer `/Users/yunes/Documents/New project/AM1_projet/.env`:

```env
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
ADMIN_TOKEN=...
# optionnel
SUPABASE_IMAGE_BUCKET=scan-images
```

## Lancer l'application
```bash
source .venv/bin/activate
python -m app.main --mode web
```

- Interface: [http://localhost:8000](http://localhost:8000)
- Docs API: [http://localhost:8000/docs](http://localhost:8000/docs)
- Admin: [http://localhost:8000/admin](http://localhost:8000/admin)

## Fonctionnalités validées
- Login Google + persistance session
- Préférences utilisateur (profil, restrictions, consentement image)
- Historique (lecture/suppression/voir)
- Favoris (ajout/lecture/suppression/voir)
- Scan image -> top-k -> recette
- Ajustement dynamique des portions côté frontend (mise à jour en direct)

## Retrain manuel du modèle (complet)
```bash
source .venv/bin/activate
python -m app.ml.retrain --data data/food --epochs 5 --batch-size 16
```

Le modèle est écrit dans `/Users/yunes/Documents/New project/AM1_projet/models/model_food.pth`.

## Retrain incrémental (batch + replay)
```bash
source .venv/bin/activate
python -m app.ml.retrain_incremental \
  --batch-dir data/auto_batches/<batch_id> \
  --base-model models/model_food.pth \
  --out models/model_food.pth \
  --data data/food \
  --epochs 2 \
  --replay-per-class 20
```

## Automatisation n8n + Admin
Workflows disponibles:
- `/Users/yunes/Documents/New project/AM1_projet/docs/n8n/foodai_n8n_cloud_free_v3_single_agent.json`
- `/Users/yunes/Documents/New project/AM1_projet/docs/n8n/foodai_n8n_cloud_free_v4_batch_two_agents.json`

Endpoints admin utilisés:
- `POST /api/admin/candidates/n8n`
- `POST /api/admin/candidates/n8n/batch`
- `GET /api/admin/candidates`
- `PATCH /api/admin/candidates/{candidate_id}`
- `POST /api/admin/retrain/incremental`
- `GET /api/admin/retrain/status`

## Troubleshooting
### `ModuleNotFoundError: dotenv`
```bash
source .venv/bin/activate
python -m pip install python-dotenv
```

### `ModuleNotFoundError: torch`
Tu n'es pas dans le bon venv ou torch n'est pas installé.

```bash
source .venv/bin/activate
python -c "import torch; print(torch.__version__)"
```

Si erreur:
```bash
python -m pip install torch torchvision
```

### Le frontend ne prend pas les changements JS
- redémarrer le backend
- hard refresh navigateur (`Cmd + Shift + R`)

## Rapport détaillé
- Markdown: `/Users/yunes/Documents/New project/AM1_projet/RAPPORT_MODIFICATIONS.md`
- PDF: `/Users/yunes/Documents/New project/AM1_projet/RAPPORT_MODIFICATIONS.pdf`
