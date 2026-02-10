from __future__ import annotations

import argparse
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from app.core.recipes import RecipeDB
from app.core.scaling import scale_dish
from app.core.units import format_quantity

console = Console()

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Get recipe for a dish and scale ingredients.")
    parser.add_argument("--dish", required=True, help="Dish id or dish name (e.g. pizza_margherita)")
    parser.add_argument("--servings", type=int, default=None, help="Number of servings (int >= 1)")
    args = parser.parse_args(argv)

    db = RecipeDB.load()
    dish = db.find_dish(args.dish)

    if dish is None:
        suggestions = db.suggest(args.dish)
        msg = f"Plat introuvable: '{args.dish}'."
        if suggestions:
            msg += "\n\nSuggestions:\n" + "\n".join([f"- {d.id} ({d.name})" for d in suggestions])
        console.print(Panel(msg, title="Erreur", style="red"))
        return 2

    servings = args.servings if args.servings is not None else dish.servings_default
    scaled = scale_dish(dish, servings)

    console.print(Panel(f"[bold]{scaled.name}[/bold]\nPortions: {servings}", title="Résultat", style="green"))

    table = Table(title="Ingrédients", show_header=True, header_style="bold")
    table.add_column("Quantité", justify="right")
    table.add_column("Ingrédient")

    for ing in scaled.ingredients:
        table.add_row(format_quantity(ing.qty, ing.unit), ing.display)

    console.print(table)

    console.print("\n[bold]Étapes[/bold]")
    for i, step in enumerate(scaled.steps, start=1):
        console.print(f"{i}. {step}")

    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
