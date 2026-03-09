from __future__ import annotations

from pathlib import Path
import argparse

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models
from tqdm import tqdm


def accuracy_from_logits(logits: torch.Tensor, y: torch.Tensor) -> float:
    preds = logits.argmax(dim=1)
    return (preds == y).float().mean().item()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default="data/food")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--out", type=str, default="models/model_food.pth")
    parser.add_argument("--num_workers", type=int, default=0)  # macOS: 0 souvent plus safe
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Device:", device)

    # Transforms
    train_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(10),
        transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.10),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])

    val_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])

    train_root = Path(args.data) / "train"
    val_root = Path(args.data) / "val"

    train_ds = datasets.ImageFolder(train_root, transform=train_tf)
    val_ds = datasets.ImageFolder(val_root, transform=val_tf)

    num_classes = len(train_ds.classes)
    print("Classes:", train_ds.classes)

    train_loader = DataLoader(
        train_ds, batch_size=args.batch_size, shuffle=True,
        num_workers=args.num_workers, pin_memory=(device.type == "cuda")
    )
    val_loader = DataLoader(
        val_ds, batch_size=args.batch_size, shuffle=False,
        num_workers=args.num_workers, pin_memory=(device.type == "cuda")
    )

    # Model : ResNet18 pretrained
    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)

    # 1) Freeze tout
    for p in model.parameters():
        p.requires_grad = False

    # 2) Remplacer la tête classifier (fc)
    model.fc = nn.Linear(model.fc.in_features, num_classes)

    # 3) Unfreeze layer4 + fc (fine-tuning léger)
    for p in model.layer4.parameters():
        p.requires_grad = True
    for p in model.fc.parameters():
        p.requires_grad = True

    model.to(device)

    criterion = nn.CrossEntropyLoss()

    # Optimizer: AdamW sur SEULEMENT les params entraînables
    optimizer = optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=args.lr,
        weight_decay=1e-4
    )

    # Scheduler: stabilise et aide la généralisation
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    for epoch in range(1, args.epochs + 1):
        # ---- TRAIN
        model.train()
        train_ok = 0
        train_total = 0

        for imgs, labels in tqdm(train_loader, desc=f"Train {epoch}", leave=False):
            imgs, labels = imgs.to(device), labels.to(device)

            optimizer.zero_grad(set_to_none=True)
            logits = model(imgs)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()

            preds = logits.argmax(dim=1)
            train_ok += (preds == labels).sum().item()
            train_total += labels.size(0)

        train_acc = train_ok / max(1, train_total)

        # ---- VAL
        model.eval()
        val_ok = 0
        val_total = 0
        with torch.no_grad():
            for imgs, labels in val_loader:
                imgs, labels = imgs.to(device), labels.to(device)
                logits = model(imgs)
                preds = logits.argmax(dim=1)
                val_ok += (preds == labels).sum().item()
                val_total += labels.size(0)

        val_acc = val_ok / max(1, val_total)

        scheduler.step()

        print(f"Epoch {epoch}/{args.epochs} | train_acc={train_acc:.3f} | val_acc={val_acc:.3f}")

    # Save
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    torch.save({
        "model_state": model.state_dict(),
        "classes": train_ds.classes
    }, args.out)

    print("Model saved to:", args.out)


if __name__ == "__main__":
    main()
