from __future__ import annotations

import argparse
from PIL import Image

import torch
import torch.nn as nn
from torchvision import transforms, models

from app.core.recipes import RecipeDB
from app.core.scaling import scale_dish
from app.core.units import format_quantity


def load_model(model_path: str, device: torch.device):
    ckpt = torch.load(model_path, map_location=device)
    classes = ckpt["classes"]

    model = models.resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, len(classes))
    model.load_state_dict(ckpt["model_state"])
    model.to(device)
    model.eval()
    return model, classes


def predict_topk(model, classes, image_path: str, device: torch.device, k: int = 2):
    tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])

    img = Image.open(image_path).convert("RGB")
    x = tf(img).unsqueeze(0).to(device)

    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1)[0]
        topk = torch.topk(probs, k=min(k, len(classes)))

    return [(classes[idx], float(score))
            for score, idx in zip(topk.values, topk.indices)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="models/model_food.pth")
    parser.add_argument("--image", type=str, required=True)
    parser.add_argument("--servings", type=int, default=2)

    # 🔹 NOUVEAU
    parser.add_argument("--min_conf", type=float, default=0.60,
                        help="Seuil minimum de confiance pour afficher la recette")

    parser.add_argument("--reject_label", type=str, default="other",
                        help="Label à rejeter (classe inconnue)")

    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, classes = load_model(args.model, device)

    top = predict_topk(model, classes, args.image, device, k=2)

    print("=== PREDICTION (top-2) ===")
    for name, conf in top:
        print(f"- {name}: {conf:.3f}")

    dish_id, conf = top[0]
    print(f"\nPredicted: {dish_id} (confidence={conf:.3f})")

    # 🔹 REJET PAR CONFIANCE
    if conf < args.min_conf:
        print(
            f"\n=> Incertain (conf={conf:.3f} < seuil={args.min_conf:.2f})\n"
            "=> Conseil : reprendre la photo (plat centré, bonne lumière, fond simple).\n"
            "=> Aucune recette affichée."
        )
        return

    # 🔹 REJET PAR LABEL
    if dish_id == args.reject_label:
        print(f"=> Classe rejetée ('{args.reject_label}'): pas de recette affichée.")
        return

    db = RecipeDB.load()
    dish = db.find_dish(dish_id)

    if dish is None:
        print("=> Plat prédit mais introuvable dans recipes.json")
        print("=> Vérifie que l'id du dossier == l'id dans recipes.json")
        return

    scaled = scale_dish(dish, args.servings)

    print(f"\n=== RECETTE: {scaled.name} | Portions: {args.servings} ===\n")

    print("Ingrédients:")
    for ing in scaled.ingredients:
        print(f"- {format_quantity(ing.qty, ing.unit)} {ing.display}")

    print("\nÉtapes:")
    for i, s in enumerate(scaled.steps, 1):
        print(f"{i}. {s}")


if __name__ == "__main__":
    main()
