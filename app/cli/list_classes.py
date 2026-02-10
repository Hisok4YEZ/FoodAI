from __future__ import annotations

from app.core.recipes import RecipeDB

def main() -> None:
    db = RecipeDB.load()
    for d in db.dishes:
        print(d.id)

if __name__ == "__main__":
    main()
