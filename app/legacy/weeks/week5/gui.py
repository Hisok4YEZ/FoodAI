from __future__ import annotations

import sys
from pathlib import Path
import argparse

# Imports FastAPI au niveau module pour éviter les ForwardRef
try:
    from fastapi import FastAPI, File, HTTPException, UploadFile
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse
    from pydantic import BaseModel
    from typing import List, Optional
    import shutil
    import tempfile
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

# Mode déterminé par argument
MODE = None  # Sera défini par les arguments


def run_pyqt():
    """Lance l'interface PyQt6"""
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

    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


def run_web():
    """Lance le backend web FastAPI"""
    if not FASTAPI_AVAILABLE:
        print("❌ FastAPI n'est pas installé. Installez-le avec:")
        print("   pip install fastapi uvicorn python-multipart pydantic")
        sys.exit(1)
    
    from app.core.recipes import RecipeDB
    from app.core.scaling import scale_dish
    from app.core.units import format_quantity
    from app.week5.predictor import FoodPredictor

    # Initialisation FastAPI
    app = FastAPI(
        title="FoodAI API",
        description="API de reconnaissance de plats par IA",
        version="1.0.0"
    )

    # Configuration CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Chargement des modèles au démarrage
    print("🔄 Chargement du modèle et de la base de recettes...")
    try:
        predictor = FoodPredictor(model_path="models/model_food.pth")
        db = RecipeDB.load()
        print("✅ Modèle et base de données chargés avec succès !")
    except Exception as e:
        print(f"❌ Erreur lors du chargement : {e}")
        predictor = None
        db = None

    # Modèles Pydantic
    class PredictionResponse(BaseModel):
        label: str
        confidence: float

    class IngredientResponse(BaseModel):
        name: str
        display: str
        qty: float
        unit: str
        formatted: str

    class RecipeResponse(BaseModel):
        id: str
        name: str
        servings: int
        ingredients: List[IngredientResponse]
        steps: List[str]

    class FullPredictionResponse(BaseModel):
        predictions: List[PredictionResponse]
        recipe: Optional[RecipeResponse]
        warning: Optional[str]

    @app.get("/")
    async def root():
        """Page d'accueil - sert l'interface HTML"""
        html_path = Path(__file__).parent / "web_interface.html"
        if html_path.exists():
            return FileResponse(html_path)
        return {
            "message": "Bienvenue sur FoodAI API 🍽️",
            "status": "ok" if predictor and db else "error",
            "info": "Créez un fichier web_interface.html dans app/week5/ pour voir l'interface web"
        }

    @app.get("/health")
    async def health_check():
        """Vérifier que l'API fonctionne"""
        return {
            "status": "healthy",
            "predictor_loaded": predictor is not None,
            "db_loaded": db is not None,
            "num_dishes": len(db.dishes) if db else 0
        }

    @app.post("/api/predict", response_model=FullPredictionResponse)
    async def predict(
        file: UploadFile = File(...),
        servings: int = 2,
        min_confidence: float = 0.70
    ):
        """Prédire le plat à partir d'une image et retourner la recette"""
        print(f"📸 Nouvelle prédiction - Fichier: {file.filename}, Portions: {servings}, Seuil: {min_confidence}")
        
        if not predictor or not db:
            raise HTTPException(
                status_code=503,
                detail="Le modèle n'est pas chargé. Vérifiez que le fichier model_food.pth existe."
            )
        
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="Le fichier doit être une image"
            )
        
        tmp_path = None
        try:
            # Sauvegarder le fichier temporairement
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
                shutil.copyfileobj(file.file, tmp_file)
                tmp_path = tmp_file.name
            
            print(f"🔍 Analyse de l'image: {tmp_path}")
            
            # Prédiction
            predictions = predictor.predict_topk(tmp_path, k=3)
            print(f"✅ Top-3: {[(p.label, f'{p.confidence:.3f}') for p in predictions]}")
            
            predictions_data = [
                PredictionResponse(label=p.label, confidence=p.confidence)
                for p in predictions
            ]
            
            best = predictions[0]
            recipe_data = None
            warning = None
            
            if best.confidence < min_confidence:
                warning = f"Prédiction incertaine (confiance={best.confidence:.3f} < seuil={min_confidence:.2f})"
                print(f"⚠️ {warning}")
            else:
                dish = db.find_dish(best.label)
                
                if dish is None:
                    warning = f"Plat prédit '{best.label}' introuvable dans la base de recettes"
                    print(f"⚠️ {warning}")
                else:
                    print(f"📖 Recette trouvée: {dish.name}")
                    scaled = scale_dish(dish, servings)
                    
                    ingredients_data = [
                        IngredientResponse(
                            name=ing.name,
                            display=ing.display,
                            qty=ing.qty,
                            unit=ing.unit,
                            formatted=format_quantity(ing.qty, ing.unit)
                        )
                        for ing in scaled.ingredients
                    ]
                    
                    recipe_data = RecipeResponse(
                        id=scaled.id,
                        name=scaled.name,
                        servings=servings,
                        ingredients=ingredients_data,
                        steps=scaled.steps
                    )
            
            return FullPredictionResponse(
                predictions=predictions_data,
                recipe=recipe_data,
                warning=warning
            )
        
        except HTTPException:
            raise
        except Exception as e:
            print(f"❌ Erreur lors de la prédiction: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de la prédiction: {str(e)}"
            )
        
        finally:
            # Nettoyer le fichier temporaire
            if tmp_path:
                try:
                    Path(tmp_path).unlink()
                except Exception as e:
                    print(f"⚠️ Erreur lors de la suppression du fichier temporaire: {e}")

    @app.get("/api/dishes")
    async def list_dishes():
        """Lister tous les plats disponibles dans la base"""
        if not db:
            raise HTTPException(status_code=503, detail="Base de données non chargée")
        
        return {
            "total": len(db.dishes),
            "dishes": [
                {"id": d.id, "name": d.name, "servings_default": d.servings_default}
                for d in db.dishes
            ]
        }

    print("🚀 Démarrage du serveur FastAPI...")
    print("📍 L'API sera accessible sur : http://localhost:8000")
    print("📚 Documentation interactive : http://localhost:8000/docs")
    print("🌐 Interface web : http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)


def main():
    parser = argparse.ArgumentParser(description="Lanceur de l'application FoodAI")
    parser.add_argument(
        '--mode',
        choices=['pyqt', 'web'],
        default='pyqt',
        help='Mode d\'interface : pyqt (bureau) ou web (navigateur)'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'web':
        print("🌐 Lancement en mode WEB...")
        run_web()
    else:
        print("🖥️ Lancement en mode PyQt6...")
        run_pyqt()


if __name__ == "__main__":
    main()