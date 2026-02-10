from __future__ import annotations

from dataclasses import dataclass
from typing import List

from PIL import Image

import torch
import torch.nn as nn
from torchvision import transforms, models


@dataclass(frozen=True)
class Prediction:
    label: str
    confidence: float


class FoodPredictor:
    def __init__(self, model_path: str = "models/model_food.pth", device: str | None = None):
        self.device = torch.device(device) if device else torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_path = model_path
        self.model, self.classes = self._load_model(model_path)

        self.tf = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ])

    def _load_model(self, model_path: str):
        ckpt = torch.load(model_path, map_location=self.device)
        classes = ckpt["classes"]

        model = models.resnet18(weights=None)
        model.fc = nn.Linear(model.fc.in_features, len(classes))
        model.load_state_dict(ckpt["model_state"])
        model.to(self.device)
        model.eval()
        return model, classes

    def predict_topk(self, image_path: str, k: int = 3) -> List[Prediction]:
        img = Image.open(image_path).convert("RGB")
        x = self.tf(img).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(x)
            probs = torch.softmax(logits, dim=1)[0]
            topk = torch.topk(probs, k=min(k, len(self.classes)))

        preds: List[Prediction] = []
        for score, idx in zip(topk.values.tolist(), topk.indices.tolist()):
            preds.append(Prediction(label=self.classes[idx], confidence=float(score)))
        return preds
