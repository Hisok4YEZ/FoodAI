from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QFileDialog,
    QVBoxLayout, QHBoxLayout, QTextEdit, QSpinBox, QDoubleSpinBox,
    QMessageBox, QGroupBox, QFormLayout
)

from app.core.recipes import RecipeDB
from app.core.scaling import scale_dish
from app.core.units import format_quantity
from app.week5.predictor import FoodPredictor


def pretty_recipe(dish, servings: int) -> str:
    scaled = scale_dish(dish, servings)
    lines = []
    lines.append(f"=== RECETTE: {scaled.name} | Portions: {servings} ===\n")

    lines.append("Ingrédients:")
    for ing in scaled.ingredients:
        lines.append(f"- {format_quantity(ing.qty, ing.unit)} {ing.display}")

    lines.append("\nÉtapes:")
    for i, s in enumerate(scaled.steps, 1):
        lines.append(f"{i}. {s}")

    return "\n".join(lines)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AM1 — Photo → Plat → Recette")
        self.resize(900, 600)

        # Core
        self.db = RecipeDB.load()
        self.predictor = FoodPredictor(model_path="models/model_food.pth")

        self.current_image_path: str | None = None
        self.current_topk = None  # type: ignore

        # --- UI
        self.btn_open = QPushButton("Choisir une image")
        self.btn_open.clicked.connect(self.pick_image)

        self.img_label = QLabel("Aucune image sélectionnée")
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_label.setFixedSize(360, 360)
        self.img_label.setStyleSheet("border: 1px solid #999; background: #fafafa;")

        # Controls group
        controls = QGroupBox("Paramètres")
        form = QFormLayout()

        self.spin_servings = QSpinBox()
        self.spin_servings.setRange(1, 20)
        self.spin_servings.setValue(2)
        self.spin_servings.valueChanged.connect(self.refresh_output)

        self.spin_minconf = QDoubleSpinBox()
        self.spin_minconf.setDecimals(2)
        self.spin_minconf.setRange(0.0, 1.0)
        self.spin_minconf.setSingleStep(0.05)
        self.spin_minconf.setValue(0.70)
        self.spin_minconf.valueChanged.connect(self.refresh_output)

        form.addRow("Portions :", self.spin_servings)
        form.addRow("Seuil confiance :", self.spin_minconf)
        controls.setLayout(form)

        # Outputs
        self.topk_label = QLabel("Top-3 : (aucune prédiction)")
        self.topk_label.setWordWrap(True)

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setPlaceholderText("Ici s'affichera la recette si la prédiction est suffisamment sûre.")

        # Layout
        left = QVBoxLayout()
        left.addWidget(self.btn_open)
        left.addWidget(self.img_label, alignment=Qt.AlignmentFlag.AlignTop)
        left.addWidget(controls)
        left.addStretch(1)

        right = QVBoxLayout()
        right.addWidget(self.topk_label)
        right.addWidget(self.text)

        root = QHBoxLayout()
        root.addLayout(left, 0)
        root.addLayout(right, 1)
        self.setLayout(root)

    def pick_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choisir une image",
            "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if not path:
            return

        self.current_image_path = path
        self.show_image(path)
        self.run_prediction_and_display()

    def show_image(self, path: str):
        pix = QPixmap(path)
        if pix.isNull():
            QMessageBox.warning(self, "Erreur", "Impossible de charger l'image.")
            return

        # Fit image inside label
        pix = pix.scaled(self.img_label.width(), self.img_label.height(), Qt.AspectRatioMode.KeepAspectRatio,
                         Qt.TransformationMode.SmoothTransformation)
        self.img_label.setPixmap(pix)

    def run_prediction_and_display(self):
        if not self.current_image_path:
            return

        topk = self.predictor.predict_topk(self.current_image_path, k=3)
        self.current_topk = topk
        self.refresh_output()

    def refresh_output(self):
        if not self.current_image_path or not self.current_topk:
            return

        servings = int(self.spin_servings.value())
        min_conf = float(self.spin_minconf.value())

        # Display topk
        lines = ["=== PREDICTION (top-3) ==="]
        for p in self.current_topk:
            lines.append(f"- {p.label}: {p.confidence:.3f}")
        self.topk_label.setText("\n".join(lines))

        # Decision
        best = self.current_topk[0]
        if best.confidence < min_conf:
            self.text.setPlainText(
                f"⚠️ Prédiction incertaine (conf={best.confidence:.3f} < seuil={min_conf:.2f}).\n\n"
                "Conseils :\n"
                "- plat bien centré\n"
                "- bonne lumière\n"
                "- fond simple (pas de mains/packaging)\n"
                "- éviter de trop zoomer\n\n"
                "Aucune recette affichée."
            )
            return

        dish = self.db.find_dish(best.label)
        if dish is None:
            self.text.setPlainText(
                "Plat prédit mais introuvable dans recipes.json.\n"
                "Vérifie que l'id de la classe == l'id dans recipes.json."
            )
            return

        self.text.setPlainText(pretty_recipe(dish, servings))


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
