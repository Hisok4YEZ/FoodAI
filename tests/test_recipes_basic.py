from app.core.recipes import RecipeDB

def test_load_and_find():
    db = RecipeDB.load()
    assert len(db.dishes) >= 1

    d1 = db.find_dish("pizza_margherita")
    assert d1 is not None
    assert d1.id == "pizza_margherita"

    d2 = db.find_dish("Pizza Margherita")
    assert d2 is not None
    assert d2.id == "pizza_margherita"

def test_suggest():
    db = RecipeDB.load()
    s = db.suggest("pizza")
    assert isinstance(s, list)
