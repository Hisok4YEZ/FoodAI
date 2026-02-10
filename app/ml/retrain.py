from __future__ import annotations

import argparse
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models
from tqdm import tqdm


def build_transforms():
    train_tf = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(10),
            transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.10),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ]
    )

    eval_tf = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ]
    )
    return train_tf, eval_tf


def evaluate(model: nn.Module, loader: DataLoader, device: torch.device) -> float:
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for imgs, labels in loader:
            imgs, labels = imgs.to(device), labels.to(device)
            logits = model(imgs)
            preds = logits.argmax(dim=1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)
    return correct / max(1, total)


def main():
    parser = argparse.ArgumentParser(description="Retrain FoodAI model on local dataset.")
    parser.add_argument("--data", type=str, default="data/food", help="Dataset root containing train/val/test")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--out", type=str, default="models/model_food.pth")
    parser.add_argument("--skip-test", action="store_true", help="Skip test split evaluation")
    args = parser.parse_args()

    data_root = Path(args.data)
    train_root = data_root / "train"
    val_root = data_root / "val"
    test_root = data_root / "test"

    if not train_root.exists() or not val_root.exists():
        raise SystemExit(f"Missing dataset folders. Expected: {train_root} and {val_root}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    train_tf, eval_tf = build_transforms()
    train_ds = datasets.ImageFolder(train_root, transform=train_tf)
    val_ds = datasets.ImageFolder(val_root, transform=eval_tf)

    num_classes = len(train_ds.classes)
    print(f"Classes ({num_classes}): {train_ds.classes}")

    train_loader = DataLoader(
        train_ds,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=(device.type == "cuda"),
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=(device.type == "cuda"),
    )

    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    for p in model.parameters():
        p.requires_grad = False

    model.fc = nn.Linear(model.fc.in_features, num_classes)
    for p in model.layer4.parameters():
        p.requires_grad = True
    for p in model.fc.parameters():
        p.requires_grad = True
    model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=args.lr,
        weight_decay=1e-4,
    )
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    for epoch in range(1, args.epochs + 1):
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
        val_acc = evaluate(model, val_loader, device)
        scheduler.step()

        print(f"Epoch {epoch}/{args.epochs} | train_acc={train_acc:.3f} | val_acc={val_acc:.3f}")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    torch.save({"model_state": model.state_dict(), "classes": train_ds.classes}, args.out)
    print(f"Model saved to: {args.out}")

    if not args.skip_test and test_root.exists():
        test_ds = datasets.ImageFolder(test_root, transform=eval_tf)
        test_loader = DataLoader(
            test_ds,
            batch_size=args.batch_size,
            shuffle=False,
            num_workers=args.num_workers,
            pin_memory=(device.type == "cuda"),
        )
        test_acc = evaluate(model, test_loader, device)
        print(f"Test accuracy: {test_acc:.3f}")
    elif not args.skip_test:
        print(f"Test split not found: {test_root} (skipped)")


if __name__ == "__main__":
    main()

