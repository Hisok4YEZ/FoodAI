from __future__ import annotations

from dataclasses import replace
from typing import List

from .recipes import Dish, Ingredient

# ingrédients "en pièce" qu'on arrondit toujours à l'entier
ALWAYS_INTEGER_PIECES = {
    "pate_a_pizza",
    "pains_burger",
    "steaks_haches",
    "fromage_tranches",
    "nori"
}

def round_for_unit(qty: float, unit: str, ing_name: str) -> float:
    if unit in {"g", "ml"}:
        return round(qty)
    if unit in {"kg", "l"}:
        return round(qty, 2)
    if unit == "piece":
        if ing_name in ALWAYS_INTEGER_PIECES:
            return max(1.0, float(round(qty)))  # au moins 1
        return round(qty * 2) / 2.0
    if unit in {"tbsp", "tsp"}:
        return round(qty * 4) / 4.0
    return qty

def scale_dish(dish: Dish, servings: int) -> Dish:
    if servings < 1:
        raise ValueError("servings must be >= 1")

    factor = servings / dish.servings_default

    new_ings: List[Ingredient] = []
    for ing in dish.ingredients:
        new_qty = ing.qty * factor
        new_qty = round_for_unit(new_qty, ing.unit, ing.name)

        if new_qty <= 0:
            new_qty = ing.qty * factor

        new_ings.append(replace(ing, qty=new_qty))

    return replace(dish, servings_default=servings, ingredients=new_ings)
