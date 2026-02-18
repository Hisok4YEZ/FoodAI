# Rapport des modifications FoodAI

Date de mise à jour: 2026-02-18
Projet: `/Users/yunes/Documents/New project/AM1_projet`
Branche: `feature/leo`

## 1) Objectif de cette passe
Stabiliser l'application web sur une version fonctionnelle et conserver les fonctionnalités produit clés:
- authentification Google via Supabase
- historique utilisateur
- favoris utilisateur
- affichage recette
- mise à jour dynamique des portions en UI

Cette passe a volontairement remis de côté les ajouts d'automatisation avancée pour revenir à une base stable et exploitable.

---

## 2) Synthèse des actions effectuées
### 2.1 Retour à une base stable
Le code a été ramené à un état antérieur stable (avant les couches d'automatisation n8n/retrain admin avancées) afin de:
- supprimer les régressions API observées
- réduire la complexité opérationnelle
- revenir à un comportement prévisible côté UI et backend

### 2.2 Diagnostic environnement Python
Des erreurs d'exécution ont été identifiées côté machine locale:
- `ModuleNotFoundError: dotenv`
- `ModuleNotFoundError: torch`

Cause probable:
- exécution hors environnement virtuel prévu
- mismatch version Python système (3.9) vs dépendances ML

Correctif recommandé:
- recréer un venv en Python 3.10
- réinstaller les dépendances dans ce venv

### 2.3 Correctif UX: portions en direct
Problème signalé:
- le changement de `servings` ne mettait plus la recette à jour immédiatement

Correction appliquée:
- conservation d'une recette de référence (base) côté frontend
- application d'un ratio de scaling en direct
- rafraîchissement instantané sur saisie (`oninput`) et non plus seulement sur perte de focus (`onchange`)

Impact utilisateur:
- modification des portions visible immédiatement
- suppression du besoin de rescanner pour voir les quantités adaptées

---

## 3) Détail technique des modifications

## 3.1 Frontend (`app/web/static/js/app.js`)
### Ajouts principaux
- variables globales de base recette:
  - `recipeBase`
  - `recipeBaseServings`

### Flux prédiction
Après réponse `/api/predict`:
- `currentResponse` reste la réponse brute
- `recipeBase` est clonée depuis `data.recipe`
- `recipeBaseServings` est mémorisé

### Flux favoris/historique
- Favoris: si recette présente, elle devient nouvelle base de scaling
- Historique sans recette: reset de la base pour éviter affichage incohérent

### `refreshRecipeDisplay()`
Nouveau comportement:
1. lit `requestedServings`
2. calcule `ratio = requestedServings / baseServings`
3. rescales les `qty` ingrédients
4. reformate les unités (`g->kg`, `ml->l`, pluralisation `piece/pieces`)
5. reconstruit le texte recette affiché

Résultat:
- cohérence de l'affichage même quand l'utilisateur ajuste plusieurs fois les portions

## 3.2 Template (`app/web/templates/index.html`)
Changements:
- `servings`: `onchange` -> `oninput`
- `confidence`: `onchange` -> `oninput`

Effet:
- feedback immédiat pendant la saisie

---

## 4) État fonctionnel attendu après ces changements
- login Google: OK
- ouverture app post-login: OK
- upload image: OK
- prédiction + recette: OK (si classe connue)
- changement portions: OK (mise à jour immédiate)
- favoris: OK
- historique: OK

Précondition:
- backend lancé dans le bon environnement Python

---

## 5) Procédure d'exécution validée
Depuis `/Users/yunes/Documents/New project/AM1_projet`:

```bash
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m app.main --mode web
```

URL:
- app: [http://localhost:8000](http://localhost:8000)
- docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 6) Risques résiduels et points de vigilance
1. **Dépendances lourdes ML**
- installation lente/fragile selon version Python locale

2. **Cache navigateur**
- une ancienne version JS peut masquer le correctif portions

3. **Données recettes**
- si une classe n'existe pas dans `recipes.json`, pas de recette détaillée

---

## 7) Checklist QA recommandée
1. Connexion Google
2. Scan image d'un plat connu
3. Modifier `servings` (2 -> 5 -> 1)
4. Vérifier que quantités changent à chaque étape
5. Ajouter en favori puis recharger favori
6. Vérifier que le rescaling fonctionne aussi depuis un favori

---

## 8) Conclusion
La priorité "revenir à une version qui marche" est respectée:
- code recentré sur un socle stable
- comportement portions restauré en dynamique
- documentation renforcée pour installation et maintenance
