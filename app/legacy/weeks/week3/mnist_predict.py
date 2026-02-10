from __future__ import annotations

import argparse
import random

import torch
import torch.nn as nn
from torchvision import datasets, transforms
import matplotlib.pyplot as plt

class SimpleCNN(nn.Module):
    def __init__(self, num_classes: int = 10) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(32 * 7 * 7, 128),
            nn.ReLU(),
            nn.Linear(128, num_classes)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.features(x))

@torch.no_grad()
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="models/model_mnist.pth")
    parser.add_argument("--index", type=int, default=-1, help="Index in test set (-1=random)")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])

    test_ds = datasets.MNIST(root="data", train=False, download=True, transform=transform)

    idx = args.index if args.index >= 0 else random.randint(0, len(test_ds) - 1)
    img, true_label = test_ds[idx]

    model = SimpleCNN().to(device)
    ckpt = torch.load(args.model, map_location=device)
    model.load_state_dict(ckpt["model_state"])
    model.eval()

    x = img.unsqueeze(0).to(device)  # (1,1,28,28)
    logits = model(x)
    probs = torch.softmax(logits, dim=1).squeeze(0).cpu()
    pred = int(torch.argmax(probs).item())
    conf = float(probs[pred].item())

    print(f"Index: {idx}")
    print(f"True label: {true_label}")
    print(f"Pred label: {pred} (confidence={conf:.4f})")

    # Afficher l'image (sans normalisation)
    # Recharger en ToTensor uniquement pour affichage propre :
    raw_test_ds = datasets.MNIST(root="data", train=False, download=True, transform=transforms.ToTensor())
    raw_img, _ = raw_test_ds[idx]
    plt.imshow(raw_img.squeeze(0), cmap="gray")
    plt.title(f"True={true_label} | Pred={pred} ({conf:.2f})")
    plt.axis("off")
    plt.show()

if __name__ == "__main__":
    main()
