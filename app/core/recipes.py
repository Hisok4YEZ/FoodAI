from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .units import ALLOWED_UNITS

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "recipes.json"

@dataclass(frozen=True)
class Ingredient:
    name: str
    display: str
    qty: float
    unit: str

@dataclass(frozen=True)
class Dish:
    id: str
    name: str
    servings_default: int
    ingredients: List[Ingredient]
    steps: List[str]

class RecipeDB:
    def __init__(self, dishes: List[Dish]) -> None:
        self.dishes = dishes
        self.by_id = {d.id: d for d in dishes}
        self.by_name_lower = {d.name.lower(): d for d in dishes}

    @staticmethod
    def load(path: Path = DATA_PATH) -> "RecipeDB":
        raw = json.loads(path.read_text(encoding="utf-8"))
        validate_recipes_json(raw)

        dishes: List[Dish] = []
        for d in raw["dishes"]:
            ings = [
                Ingredient(
                    name=ing["name"],
                    display=ing["display"],
                    qty=float(ing["qty"]),
                    unit=ing["unit"],
                )
                for ing in d["ingredients"]
            ]
            dishes.append(
                Dish(
                    id=d["id"],
                    name=d["name"],
                    servings_default=int(d["servings_default"]),
                    ingredients=ings,
                    steps=list(d["steps"]),
                )
            )
        return RecipeDB(dishes)

    def find_dish(self, dish_query: str) -> Optional[Dish]:
        q = dish_query.strip()
        if not q:
            return None

        if q in self.by_id:
            return self.by_id[q]

        ql = q.lower()
        if ql in self.by_name_lower:
            return self.by_name_lower[ql]

        candidates = [d for d in self.dishes if ql in d.name.lower() or ql in d.id.lower()]
        if len(candidates) == 1:
            return candidates[0]
        return None

    def suggest(self, dish_query: str, limit: int = 5) -> List[Dish]:
        ql = dish_query.strip().lower()
        if not ql:
            return []
        candidates = [d for d in self.dishes if ql in d.name.lower() or ql in d.id.lower()]
        return candidates[:limit]

def validate_recipes_json(raw: Dict[str, Any]) -> None:
    if not isinstance(raw, dict):
        raise ValueError("recipes.json: root must be an object")

    if "version" not in raw or raw["version"] != 1:
        raise ValueError("recipes.json: 'version' must exist and equal 1")

    dishes = raw.get("dishes")
    if not isinstance(dishes, list) or len(dishes) == 0:
        raise ValueError("recipes.json: 'dishes' must be a non-empty list")

    seen_ids = set()
    for i, d in enumerate(dishes):
        if not isinstance(d, dict):
            raise ValueError(f"Dish[{i}] must be an object")

        for k in ("id", "name", "servings_default", "ingredients", "steps"):
            if k not in d:
                raise ValueError(f"Dish[{i}] missing key '{k}'")

        dish_id = d["id"]
        if not isinstance(dish_id, str) or not dish_id:
            raise ValueError(f"Dish[{i}].id must be a non-empty string")
        if dish_id in seen_ids:
            raise ValueError(f"Duplicate dish id: {dish_id}")
        seen_ids.add(dish_id)

        if not isinstance(d["name"], str) or not d["name"]:
            raise ValueError(f"Dish[{i}].name must be a non-empty string")

        sd = d["servings_default"]
        if not isinstance(sd, int) or sd < 1:
            raise ValueError(f"Dish[{i}].servings_default must be an int >= 1")

        ings = d["ingredients"]
        if not isinstance(ings, list) or len(ings) == 0:
            raise ValueError(f"Dish[{i}].ingredients must be a non-empty list")

        for j, ing in enumerate(ings):
            if not isinstance(ing, dict):
                raise ValueError(f"Dish[{i}].ingredients[{j}] must be an object")
            for k in ("name", "display", "qty", "unit"):
                if k not in ing:
                    raise ValueError(f"Dish[{i}].ingredients[{j}] missing '{k}'")

            if not isinstance(ing["name"], str) or not ing["name"]:
                raise ValueError(f"Dish[{i}].ingredients[{j}].name invalid")
            if not isinstance(ing["display"], str) or not ing["display"]:
                raise ValueError(f"Dish[{i}].ingredients[{j}].display invalid")

            qty = ing["qty"]
            if not isinstance(qty, (int, float)) or float(qty) <= 0:
                raise ValueError(f"Dish[{i}].ingredients[{j}].qty must be > 0")

            unit = ing["unit"]
            if unit not in ALLOWED_UNITS:
                raise ValueError(
                    f"Dish[{i}].ingredients[{j}].unit '{unit}' not allowed. "
                    f"Allowed: {sorted(ALLOWED_UNITS)}"
                )

        steps = d["steps"]
        if not isinstance(steps, list) or len(steps) == 0:
            raise ValueError(f"Dish[{i}].steps must be a non-empty list")
        if any((not isinstance(s, str) or not s.strip()) for s in steps):
            raise ValueError(f"Dish[{i}].steps must contain non-empty strings")
