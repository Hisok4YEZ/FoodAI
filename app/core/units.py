from __future__ import annotations

ALLOWED_UNITS = {"g", "kg", "ml", "l", "piece", "tbsp", "tsp"}

UNIT_LABELS = {
    "g": "g",
    "kg": "kg",
    "ml": "ml",
    "l": "l",
    "piece": "pièce",
    "tbsp": "càs",
    "tsp": "cc"
}

def _format_number(qty: float) -> str:
    if abs(qty - round(qty)) < 1e-9:
        return str(int(round(qty)))
    return f"{qty:.2f}".rstrip("0").rstrip(".")

def format_quantity(qty: float, unit: str) -> str:
    if unit not in ALLOWED_UNITS:
        return f"{qty} {unit}"

    # conversions simples
    if unit == "g" and qty >= 1000:
        qty = qty / 1000.0
        unit = "kg"
    elif unit == "ml" and qty >= 1000:
        qty = qty / 1000.0
        unit = "l"

    unit_label = UNIT_LABELS.get(unit, unit)

    # gestion pluriel simple pour "pièce"
    if unit == "piece":
        s = _format_number(qty)
        if s != "1":
            unit_label = "pièces"
        return f"{s} {unit_label}"

    return f"{_format_number(qty)} {unit_label}"
