from __future__ import annotations

import argparse
from pathlib import Path
import random
import shutil

CLASSES_10 = [
    "pizza",
    "hamburger",
    "ramen",
    "spaghetti_bolognese",
    "caesar_salad",
    "fried_rice",
    "omelette",
    "sushi",
    "ice_cream",
    "chocolate_cake",
]

IMG_EXT = ".jpg"

def read_meta_list(meta_file: Path) -> list[str]:
    lines = meta_file.read_text().strip().splitlines()
    return [ln.strip() for ln in lines if ln.strip()]

def ensure_dirs(root: Path, classes: list[str]):
    for split in ["train", "val", "test"]:
        for c in classes:
            (root / split / c).mkdir(parents=True, exist_ok=True)

def link_or_copy(src: Path, dst: Path, mode: str):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return
    if mode == "symlink":
        dst.symlink_to(src)
    elif mode == "copy":
        shutil.copy2(src, dst)
    else:
        raise ValueError("mode must be 'symlink' or 'copy'")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--food101", type=str, required=True)
    p.add_argument("--out", type=str, default="data/food101_10")
    p.add_argument("--val_ratio", type=float, default=0.1)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--mode", type=str, default="symlink", choices=["symlink", "copy"])
    args = p.parse_args()

    random.seed(args.seed)

    food101 = Path(args.food101).expanduser().resolve()
    images_root = food101 / "images"
    meta_root = food101 / "meta"

    if not images_root.exists() or not meta_root.exists():
        raise SystemExit(f"Invalid food-101 path: {food101}")

    out_root = Path(args.out).resolve()
    ensure_dirs(out_root, CLASSES_10)

    train_list = read_meta_list(meta_root / "train.txt")
    test_list  = read_meta_list(meta_root / "test.txt")

    train_list = [x for x in train_list if x.split("/")[0] in CLASSES_10]
    test_list  = [x for x in test_list if x.split("/")[0] in CLASSES_10]

    by_class = {c: [] for c in CLASSES_10}
    for x in train_list:
        c = x.split("/")[0]
        by_class[c].append(x)

    train_final, val_final = [], []
    for c, items in by_class.items():
        random.shuffle(items)
        n_val = max(1, int(len(items) * args.val_ratio))
        val_items = items[:n_val]
        tr_items = items[n_val:]
        val_final.extend(val_items)
        train_final.extend(tr_items)

    def materialize(split: str, lst: list[str]):
        for rel in lst:
            c, img_id = rel.split("/")
            src = images_root / c / f"{img_id}{IMG_EXT}"
            dst = out_root / split / c / f"{img_id}{IMG_EXT}"
            link_or_copy(src, dst, args.mode)

    print("Selected classes:", CLASSES_10)
    materialize("train", train_final)
    materialize("val", val_final)
    materialize("test", test_list)

    print("✅ Done. Dataset ready at:", out_root)

if __name__ == "__main__":
    main()
