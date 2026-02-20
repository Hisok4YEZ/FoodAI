# Rapport des modifications FoodAI

Date de mise à jour: 2026-02-18
Projet: `AM1_projet`
Branche: `feature/leo`

## 1) Objectif de cette passe
- Retirer les éléments liés à l'ancien flux d'automatisation externe.
- Uniformiser la documentation avec des chemins au format `AM1_projet/...`.
- Conserver une base stable orientée produit (scan, historique, favoris, portions dynamiques).

## 2) Changements appliqués
### 2.1 Nettoyage des références d'automatisation externe
- Suppression des workflows d'automatisation versionnés.
- Suppression des mentions d'automatisation externe dans la documentation.
- Renommage des routes d'ingestion admin pour ne plus inclure l'ancien nommage.

Routes remplacées:
- `POST /api/admin/candidates/ingest`
- `POST /api/admin/candidates/ingest/batch`

Fichiers touchés:
- `AM1_projet/app/web/server.py`
- `AM1_projet/app/web/templates/admin.html`
- `AM1_projet/README.md`

### 2.2 Documentation uniformisée
Tous les chemins documentation sont désormais exprimés en mode projet:
- `AM1_projet/...`

Plus de chemin absolu machine dans le README / rapport.

### 2.3 Correctif UX portions (déjà intégré)
- Rescaling dynamique des ingrédients côté frontend.
- Réaction immédiate via `oninput`.

Fichiers:
- `AM1_projet/app/web/static/js/app.js`
- `AM1_projet/app/web/templates/index.html`

## 3) État fonctionnel visé
- Démarrage backend rapide.
- Première prédiction potentiellement plus lente (chargement modèle).
- Historique/favoris/profil stables.
- Admin candidat/retrain utilisable sans dépendance d'automatisation externe.

## 4) Procédure d'exécution recommandée
```bash
cd "AM1_projet"
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m app.main --mode web
```

URLs:
- app: [http://localhost:8000](http://localhost:8000)
- docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- admin: [http://localhost:8000/admin](http://localhost:8000/admin)

## 5) Vérifications rapides
1. Login Google.
2. Scan image plat connu.
3. Modifier `Servings` et vérifier la mise à jour immédiate.
4. Ajouter/supprimer un favori.
5. Ouvrir l'historique et tester suppression.
6. Ouvrir admin et vérifier la liste candidats.
