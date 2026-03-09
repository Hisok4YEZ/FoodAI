from __future__ import annotations

import argparse
from PIL import Image
import torch
import torch.nn as nn
from torchvision import transforms, models

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="models/model_food.pth")
    parser.add_argument("--image", type=str, required=True)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Chargement du modèle
    ckpt = torch.load(args.model, map_location=device)
    classes = ckpt["classes"]

    model = models.resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, len(classes))
    model.load_state_dict(ckpt["model_state"])
    model.to(device)
    model.eval()

    # Prétraitement image
    tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225]),
    ])

    img = Image.open(args.image).convert("RGB")
    x = tf(img).unsqueeze(0).to(device)

    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1)[0]
        idx = probs.argmax().item()

    print("Predicted dish:", classes[idx])
    print("Confidence:", float(probs[idx]))

if __name__ == "__main__":
    main()
