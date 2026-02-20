# FoodAI

Application web de reconnaissance de plats avec:
- authentification Google (Supabase Auth)
- profil utilisateur (préférences + consentement image)
- historique des scans
- favoris
- interface admin de validation des candidats
- retrain manuel du modèle

## Structure
- `AM1_projet/app/web/` : backend FastAPI + frontend
- `AM1_projet/app/ml/` : prédiction + retrain
- `AM1_projet/app/core/` : recettes, unités, scaling
- `AM1_projet/app/data/recipes.json` : base recettes
- `AM1_projet/data/food/` : dataset d'entraînement

## Installation (recommandée)
Utilise Python 3.10.

```bash
cd "AM1_projet"
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Variables d'environnement
Créer `AM1_projet/.env`:

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
cd "AM1_projet"
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

## Endpoints admin utiles
- `POST /api/admin/candidates/ingest`
- `POST /api/admin/candidates/ingest/batch`
- `GET /api/admin/candidates`
- `PATCH /api/admin/candidates/{candidate_id}`
- `POST /api/admin/retrain/incremental`
- `GET /api/admin/retrain/status`

## Retrain manuel du modèle
```bash
cd "AM1_projet"
source .venv/bin/activate
python -m app.ml.retrain --data data/food --epochs 5 --batch-size 16
```

Modèle de sortie: `AM1_projet/models/model_food.pth`

## Retrain incrémental (batch + replay)
```bash
cd "AM1_projet"
source .venv/bin/activate
python -m app.ml.retrain_incremental \
  --batch-dir data/auto_batches/<batch_id> \
  --base-model models/model_food.pth \
  --out models/model_food.pth \
  --data data/food \
  --epochs 2 \
  --replay-per-class 20
```

## Troubleshooting
### `ModuleNotFoundError: dotenv`
```bash
source .venv/bin/activate
python -m pip install python-dotenv
```

### `ModuleNotFoundError: torch`
```bash
source .venv/bin/activate
python -c "import torch; print(torch.__version__)"
```

Si erreur:
```bash
python -m pip install torch torchvision
```

### Démarrage long / process `killed`
- éviter Python 3.13 pour ce projet
- lancer avec le venv 3.10
- hard refresh frontend après changement JS (`Cmd + Shift + R`)

## Rapports
- Markdown: `AM1_projet/RAPPORT_MODIFICATIONS.md`
- PDF: `AM1_projet/RAPPORT_MODIFICATIONS.pdf`
- PDF README: `AM1_projet/README.pdf`
