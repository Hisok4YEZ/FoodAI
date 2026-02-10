from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms, models
from tqdm import tqdm


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


class LabeledImageDataset(Dataset):
    def __init__(self, samples: List[Tuple[Path, int]], tf):
        self.samples = samples
        self.tf = tf

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label_idx = self.samples[idx]
        img = Image.open(path).convert("RGB")
        return self.tf(img), label_idx


def is_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTS


def build_transforms():
    train_tf = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(8),
            transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.08),
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


def list_images_in_class_dir(class_dir: Path) -> List[Path]:
    files = [p for p in class_dir.rglob("*") if p.is_file() and is_image(p)]
    files.sort()
    return files


def collect_batch_labels(batch_dir: Path) -> Dict[str, List[Path]]:
    out: Dict[str, List[Path]] = {}
    if not batch_dir.exists():
        return out
    for class_dir in sorted([d for d in batch_dir.iterdir() if d.is_dir()]):
        images = list_images_in_class_dir(class_dir)
        if images:
            out[class_dir.name] = images
    return out


def collect_replay_samples(
    data_root: Path,
    old_classes: List[str],
    replay_per_class: int,
) -> Dict[str, List[Path]]:
    replay: Dict[str, List[Path]] = {}
    train_root = data_root / "train"
    if not train_root.exists() or replay_per_class <= 0:
        return replay

    for cls in old_classes:
        cls_dir = train_root / cls
        if not cls_dir.exists():
            continue
        imgs = list_images_in_class_dir(cls_dir)
        if not imgs:
            continue
        if len(imgs) > replay_per_class:
            imgs = random.sample(imgs, replay_per_class)
        replay[cls] = imgs
    return replay


def evaluate(model: nn.Module, loader: DataLoader, device: torch.device) -> float:
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for imgs, labels in loader:
            imgs = imgs.to(device)
            labels = labels.to(device)
            logits = model(imgs)
            preds = logits.argmax(dim=1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)
    return correct / max(1, total)


def main():
    parser = argparse.ArgumentParser(description="Incremental retrain on new batch + replay.")
    parser.add_argument("--batch-dir", type=str, required=True, help="Folder with class subfolders and images.")
    parser.add_argument("--base-model", type=str, default="models/model_food.pth")
    parser.add_argument("--data", type=str, default="data/food")
    parser.add_argument("--out", type=str, default="models/model_food.pth")
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=5e-5)
    parser.add_argument("--replay-per-class", type=int, default=20)
    parser.add_argument("--num-workers", type=int, default=0)
    args = parser.parse_args()

    random.seed(42)
    torch.manual_seed(42)

    batch_dir = Path(args.batch_dir)
    base_model_path = Path(args.base_model)
    data_root = Path(args.data)
    out_path = Path(args.out)

    if not base_model_path.exists():
        raise SystemExit(f"Base model not found: {base_model_path}")
    if not batch_dir.exists():
        raise SystemExit(f"Batch directory not found: {batch_dir}")

    ckpt = torch.load(base_model_path, map_location="cpu")
    old_classes: List[str] = ckpt["classes"]

    batch_data = collect_batch_labels(batch_dir)
    if not batch_data:
        raise SystemExit(f"No valid images found in batch dir: {batch_dir}")

    replay_data = collect_replay_samples(data_root, old_classes, args.replay_per_class)

    classes: List[str] = list(old_classes)
    class_to_idx: Dict[str, int] = {c: i for i, c in enumerate(classes)}

    for cls_name in sorted(batch_data.keys()):
        if cls_name not in class_to_idx:
            class_to_idx[cls_name] = len(classes)
            classes.append(cls_name)

    train_samples: List[Tuple[Path, int]] = []
    for cls_name, images in batch_data.items():
        label_idx = class_to_idx[cls_name]
        train_samples.extend((img, label_idx) for img in images)

    for cls_name, images in replay_data.items():
        label_idx = class_to_idx[cls_name]
        train_samples.extend((img, label_idx) for img in images)

    if not train_samples:
        raise SystemExit("No train samples collected.")

    train_tf, eval_tf = build_transforms()
    train_ds = LabeledImageDataset(train_samples, train_tf)
    train_loader = DataLoader(
        train_ds,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=torch.cuda.is_available(),
    )

    val_root = data_root / "val"
    val_loader = None
    if val_root.exists():
        # Lightweight eval on known classes only
        val_samples: List[Tuple[Path, int]] = []
        for cls_name in old_classes:
            cls_dir = val_root / cls_name
            if not cls_dir.exists():
                continue
            images = list_images_in_class_dir(cls_dir)
            val_samples.extend((img, class_to_idx[cls_name]) for img in images[: max(1, args.replay_per_class // 2)])
        if val_samples:
            val_ds = LabeledImageDataset(val_samples, eval_tf)
            val_loader = DataLoader(
                val_ds,
                batch_size=args.batch_size,
                shuffle=False,
                num_workers=args.num_workers,
                pin_memory=torch.cuda.is_available(),
            )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    print(f"Old classes: {len(old_classes)} | New total classes: {len(classes)}")
    print(f"Batch samples: {sum(len(v) for v in batch_data.values())} | Replay samples: {sum(len(v) for v in replay_data.values())}")

    model = models.resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, len(classes))

    old_state = ckpt["model_state"]
    trunk_state = {k: v for k, v in old_state.items() if not k.startswith("fc.")}
    model.load_state_dict(trunk_state, strict=False)

    with torch.no_grad():
        old_fc_w = old_state["fc.weight"]
        old_fc_b = old_state["fc.bias"]
        for old_idx, cls_name in enumerate(old_classes):
            new_idx = class_to_idx[cls_name]
            model.fc.weight[new_idx] = old_fc_w[old_idx]
            model.fc.bias[new_idx] = old_fc_b[old_idx]

    for p in model.parameters():
        p.requires_grad = False
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
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(1, args.epochs))

    for epoch in range(1, args.epochs + 1):
        model.train()
        ok = 0
        total = 0
        epoch_loss = 0.0

        for imgs, labels in tqdm(train_loader, desc=f"Incremental train {epoch}", leave=False):
            imgs = imgs.to(device)
            labels = labels.to(device)

            optimizer.zero_grad(set_to_none=True)
            logits = model(imgs)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item() * labels.size(0)
            preds = logits.argmax(dim=1)
            ok += (preds == labels).sum().item()
            total += labels.size(0)

        scheduler.step()
        train_acc = ok / max(1, total)
        train_loss = epoch_loss / max(1, total)

        if val_loader:
            val_acc = evaluate(model, val_loader, device)
            print(f"Epoch {epoch}/{args.epochs} | loss={train_loss:.4f} | train_acc={train_acc:.3f} | val_acc={val_acc:.3f}")
        else:
            print(f"Epoch {epoch}/{args.epochs} | loss={train_loss:.4f} | train_acc={train_acc:.3f}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state": model.state_dict(),
            "classes": classes,
        },
        out_path,
    )
    print(f"Incremental model saved to: {out_path}")


if __name__ == "__main__":
    main()

