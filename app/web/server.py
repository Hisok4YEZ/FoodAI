from __future__ import annotations

import sys
from pathlib import Path
import argparse
import os
import threading
from datetime import datetime, timezone
from uuid import uuid4
from dotenv import load_dotenv

# Charge toujours le .env à la racine du projet, peu importe le dossier courant.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")


# Imports FastAPI au niveau module pour éviter les ForwardRef
try:
    from fastapi import FastAPI, File, HTTPException, UploadFile, Depends, Header, Body
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse
    from fastapi.staticfiles import StaticFiles
    from pydantic import BaseModel, ValidationError
    from typing import List, Optional, Dict, Any
    import shutil
    import tempfile
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

# Imports Supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


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
            self.predictor = FoodPredictor(model_path=str(PROJECT_ROOT / "models" / "model_food.pth"))

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
    """Lance le backend web FastAPI avec Supabase"""
    if not FASTAPI_AVAILABLE:
        print("Oups, FastAPI n'est pas installe sur cette machine.")
        print("Installe-le avec: pip install fastapi uvicorn python-multipart pydantic")
        sys.exit(1)
    
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_REDIRECT_URL = os.getenv("SUPABASE_REDIRECT_URL", "foodai://login-callback/")

    if not SUPABASE_AVAILABLE:
        print("Supabase n'est pas installe, donc je lance l'app sans authentification.")
        print("Pour l'activer: pip install supabase")
        supabase: Optional[Client] = None
    else:
        if SUPABASE_URL and SUPABASE_KEY:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("Connexion Supabase OK.")
        else:
            print("Variables SUPABASE_URL/SUPABASE_ANON_KEY manquantes, auth desactivee.")
            supabase = None
    
    from app.core.recipes import RecipeDB
    from app.core.scaling import scale_dish
    from app.core.units import format_quantity
    from app.ml.predictor import FoodPredictor

    # Initialisation FastAPI
    app = FastAPI(
        title="FoodAI API",
        description="API de reconnaissance de plats par IA avec authentification",
        version="2.0.0"
    )
    app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")

    # Configuration CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Démarrage rapide: on charge la base recettes au boot, le modèle IA à la 1ère prédiction.
    print("Je charge la base de recettes...")
    try:
        db = RecipeDB.load()
        print("Base de recettes prete.")
    except Exception as e:
        print(f"Je n'ai pas pu charger les recettes: {e}")
        db = None

    predictor = None
    predictor_error: Optional[str] = None
    predictor_lock = threading.Lock()

    def ensure_predictor_loaded():
        nonlocal predictor, predictor_error
        if predictor is not None:
            return predictor
        with predictor_lock:
            if predictor is not None:
                return predictor
            if predictor_error:
                raise RuntimeError(predictor_error)
            try:
                print("Je charge le modele IA a la demande...")
                from app.ml.predictor import FoodPredictor
                predictor = FoodPredictor(model_path=str(PROJECT_ROOT / "models" / "model_food.pth"))
                print("Modele IA charge.")
                return predictor
            except Exception as e:
                predictor_error = f"Chargement modèle impossible: {e}"
                print(f"Impossible de charger le modele: {predictor_error}")
                raise RuntimeError(predictor_error)

    # ============================================
    # MODÈLES PYDANTIC
    # ============================================
    
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

    class UserProfile(BaseModel):
        id: str
        email: str
        first_name: Optional[str]
        last_name: Optional[str]
        dietary_restrictions: List[str]
        image_storage_consent: bool
        consent_prompt_shown: bool
        created_at: str

    class UserUpdate(BaseModel):
        first_name: Optional[str] = None
        last_name: Optional[str] = None
        dietary_restrictions: Optional[List[str]] = None
        image_storage_consent: Optional[bool] = None
        consent_prompt_shown: Optional[bool] = None

    class ScanHistoryItem(BaseModel):
        id: str
        image_url: Optional[str]
        predicted_dish: str
        confidence: float
        top_predictions: List[PredictionResponse]
        servings: int
        created_at: str

    class FavoriteCreate(BaseModel):
        predicted_dish: str
        confidence: float
        top_predictions: List[PredictionResponse]
        servings: int = 2
        recipe_payload: Optional[RecipeResponse] = None

    class FavoriteItem(BaseModel):
        id: str
        predicted_dish: str
        confidence: float
        top_predictions: List[PredictionResponse]
        servings: int
        recipe_payload: Optional[RecipeResponse]
        created_at: str

    # ============================================
    # HELPERS
    # ============================================
    
    def get_user_scoped_client(access_token: str):
        """Crée un client Supabase avec le JWT utilisateur pour respecter les policies RLS."""
        if not SUPABASE_URL or not SUPABASE_KEY:
            return None
        user_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        user_client.postgrest.auth(access_token)
        return user_client

    def get_user_profile_row(user_supabase: Client, user_id: str):
        result = user_supabase.table('users').select('*').eq('id', user_id).limit(1).execute()
        if not result.data:
            return None
        return result.data[0]

    def require_user_client(current_user: Optional[Dict[str, Any]]) -> Client:
        if not current_user or not supabase:
            raise HTTPException(status_code=401, detail="Non authentifié")
        user_supabase = get_user_scoped_client(current_user["token"])
        if not user_supabase:
            raise HTTPException(status_code=500, detail="Client Supabase indisponible")
        return user_supabase

    ASSET_VERSION = str(int(datetime.now(timezone.utc).timestamp()))

    def render_html_template(template_name: str, extra_replacements: Optional[Dict[str, Any]] = None) -> str:
        html_path = Path(__file__).parent / "templates" / template_name
        if not html_path.exists():
            raise HTTPException(status_code=404, detail=f"Template introuvable: {template_name}")

        html_content = html_path.read_text(encoding="utf-8")
        replacements: Dict[str, Any] = {
            "__SUPABASE_URL__": os.getenv("SUPABASE_URL", ""),
            "__SUPABASE_ANON_KEY__": os.getenv("SUPABASE_ANON_KEY", ""),
            "__ASSET_VERSION__": ASSET_VERSION,
        }
        if extra_replacements:
            replacements.update(extra_replacements)

        for key, value in replacements.items():
            html_content = html_content.replace(key, str(value))
        return html_content

    async def get_current_user(authorization: str = Header(None)):
        """Extrait l'utilisateur du token JWT"""
        if not supabase or not authorization:
            return None
        
        try:
            token = authorization.replace("Bearer ", "")
            user = supabase.auth.get_user(token)
            if not user or not user.user:
                return None
            return {
                "id": user.user.id,
                "email": user.user.email,
                "token": token
            }
        except Exception as e:
            print(f"Je n'ai pas pu verifier le token utilisateur: {e}")
            return None

    # ============================================
    # ENDPOINTS
    # ============================================

    @app.get("/")
    async def root():
        """Page d'accueil - sert l'interface HTML"""
        try:
            return HTMLResponse(content=render_html_template("index.html"))
        except HTTPException:
            return {
                "message": "Bienvenue sur FoodAI API 🍽️",
                "status": "ok" if predictor and db else "error",
                "auth_enabled": supabase is not None
            }

    @app.get("/health")
    async def health_check():
        """Vérifier que l'API fonctionne"""
        return {
            "status": "healthy",
            "predictor_loaded": predictor is not None,
            "predictor_error": predictor_error,
            "db_loaded": db is not None,
            "num_dishes": len(db.dishes) if db else 0,
            "auth_enabled": supabase is not None
        }

    @app.get("/api/mobile/config")
    async def mobile_config():
        """Expose la configuration publique nécessaire au client mobile."""
        return {
            "supabase_url": SUPABASE_URL,
            "supabase_anon_key": SUPABASE_KEY,
            "auth_enabled": bool(SUPABASE_URL and SUPABASE_KEY and supabase is not None),
            "redirect_url": SUPABASE_REDIRECT_URL,
        }

    @app.post("/api/predict", response_model=FullPredictionResponse)
    @app.post("/api/scan", response_model=FullPredictionResponse)
    async def predict(
        file: UploadFile = File(...),
        servings: int = 2,
        min_confidence: float = 0.70,
        current_user = Depends(get_current_user)
    ):
        """Prédire le plat à partir d'une image et retourner la recette"""
        print(f"Nouvelle analyse: {file.filename} (portions={servings}, seuil={min_confidence})")
        
        if not db:
            raise HTTPException(
                status_code=503,
                detail="Base de recettes non chargée."
            )

        try:
            active_predictor = ensure_predictor_loaded()
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=str(e)
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
            
            print("Image recue, je lance l'analyse.")
            
            # Prédiction
            predictions = active_predictor.predict_topk(tmp_path, k=3)
            print(f"Predictions top-3: {[(p.label, f'{p.confidence:.3f}') for p in predictions]}")
            
            predictions_data = [
                PredictionResponse(label=p.label, confidence=p.confidence)
                for p in predictions
            ]
            
            best = predictions[0]
            recipe_data = None
            warning = None
            
            if best.confidence < min_confidence:
                warning = f"Prédiction incertaine (confiance={best.confidence:.3f} < seuil={min_confidence:.2f})"
                print(f"Confiance trop basse: {warning}")
            else:
                dish = db.find_dish(best.label)
                
                if dish is None:
                    warning = f"Plat prédit '{best.label}' introuvable dans la base de recettes"
                    print(f"Plat introuvable dans recipes: {warning}")
                else:
                    print(f"Recette trouvee: {dish.name}")
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
            
            # Sauvegarder dans l'historique si l'utilisateur est connecté
            if current_user and supabase and not warning:
                try:
                    user_supabase = get_user_scoped_client(current_user["token"])
                    if user_supabase:
                        image_url = None
                        profile_row = get_user_profile_row(user_supabase, current_user["id"])
                        keep_images = bool(profile_row.get("image_storage_consent", False)) if profile_row else False

                        if keep_images and tmp_path:
                            try:
                                bucket = os.getenv("SUPABASE_IMAGE_BUCKET", "scan-images")
                                suffix = Path(file.filename).suffix.lower() or ".jpg"
                                key = f'{current_user["id"]}/{datetime.now(timezone.utc).strftime("%Y%m%d")}/{uuid4().hex}{suffix}'
                                with open(tmp_path, "rb") as image_file:
                                    user_supabase.storage.from_(bucket).upload(
                                        key,
                                        image_file,
                                        {"content-type": file.content_type or "application/octet-stream"},
                                    )
                                image_url = key
                            except Exception as upload_error:
                                print(f"Upload image ignore (consentement actif): {upload_error}")

                        user_supabase.table('scan_history').insert({
                            'user_id': current_user["id"],
                            'image_url': image_url,
                            'predicted_dish': best.label,
                            'confidence': float(best.confidence),
                            'top_predictions': [{'label': p.label, 'confidence': p.confidence} for p in predictions_data],
                            'servings': servings
                        }).execute()
                        print(f"Scan sauvegarde pour {current_user['email']}.")
                except Exception as e:
                    print(f"Je n'ai pas pu enregistrer l'historique: {e}")
            
            return FullPredictionResponse(
                predictions=predictions_data,
                recipe=recipe_data,
                warning=warning
            )
        
        except HTTPException:
            raise
        except Exception as e:
            print(f"L'analyse a echoue: {e}")
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
                    print(f"Je n'ai pas pu supprimer le fichier temporaire: {e}")

    # ============================================
    # ENDPOINTS UTILISATEURS
    # ============================================

    @app.get("/api/user/profile", response_model=UserProfile)
    @app.get("/api/profile", response_model=UserProfile)
    async def get_user_profile(current_user = Depends(get_current_user)):
        """Obtenir le profil de l'utilisateur connecté"""
        try:
            user_supabase = require_user_client(current_user)
            result = user_supabase.table('users').select('*').eq('id', current_user["id"]).execute()
            if not result.data:
                raise HTTPException(status_code=404, detail="Profil non trouvé")
            
            user_data = result.data[0]
            dietary_restrictions = user_data.get('dietary_restrictions', [])
            if not isinstance(dietary_restrictions, list):
                dietary_restrictions = []
            return UserProfile(
                id=user_data['id'],
                email=user_data['email'],
                first_name=user_data.get('first_name'),
                last_name=user_data.get('last_name'),
                dietary_restrictions=dietary_restrictions,
                image_storage_consent=bool(user_data.get('image_storage_consent', False)),
                consent_prompt_shown=bool(user_data.get('consent_prompt_shown', False)),
                created_at=user_data['created_at']
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.patch("/api/user/profile")
    async def update_user_profile(
        payload: dict = Body(...),
        current_user = Depends(get_current_user)
    ):
        """Mettre à jour le profil utilisateur"""
        try:
            updates = UserUpdate(**payload)
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=e.errors())
        
        try:
            update_data = updates.dict(exclude_unset=True)
            if not update_data:
                raise HTTPException(status_code=400, detail="Aucune donnée à mettre à jour")
            
            user_supabase = require_user_client(current_user)
            user_supabase.table('users').update(update_data).eq('id', current_user["id"]).execute()
            return {"message": "Profil mis à jour avec succès"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/user/history", response_model=List[ScanHistoryItem])
    @app.get("/api/history", response_model=List[ScanHistoryItem])
    async def get_user_history(
        limit: int = 50,
        current_user = Depends(get_current_user)
    ):
        """Obtenir l'historique des scans de l'utilisateur"""
        try:
            user_supabase = require_user_client(current_user)
            result = user_supabase.table('scan_history')\
                .select('*')\
                .eq('user_id', current_user["id"])\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            
            return [
                ScanHistoryItem(
                    id=item['id'],
                    image_url=item.get('image_url'),
                    predicted_dish=item['predicted_dish'],
                    confidence=item['confidence'],
                    top_predictions=[PredictionResponse(**p) for p in item['top_predictions']],
                    servings=item['servings'],
                    created_at=item['created_at']
                )
                for item in result.data
            ]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/api/user/history/{scan_id}")
    @app.delete("/api/history/{scan_id}")
    async def delete_scan_from_history(
        scan_id: str,
        current_user = Depends(get_current_user)
    ):
        """Supprimer un scan de l'historique"""
        try:
            user_supabase = require_user_client(current_user)
            user_supabase.table('scan_history')\
                .delete()\
                .eq('id', scan_id)\
                .eq('user_id', current_user["id"])\
                .execute()
            return {"message": "Scan supprimé de l'historique"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/user/favorites", response_model=List[FavoriteItem])
    @app.get("/api/favorites", response_model=List[FavoriteItem])
    async def get_user_favorites(
        limit: int = 100,
        current_user = Depends(get_current_user)
    ):
        """Obtenir les favoris de l'utilisateur"""
        try:
            user_supabase = require_user_client(current_user)

            result = user_supabase.table('favorites')\
                .select('*')\
                .eq('user_id', current_user["id"])\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()

            items = result.data or []
            return [
                FavoriteItem(
                    id=item['id'],
                    predicted_dish=item['predicted_dish'],
                    confidence=item['confidence'],
                    top_predictions=[PredictionResponse(**p) for p in item['top_predictions']],
                    servings=item.get('servings', 2),
                    recipe_payload=RecipeResponse(**item['recipe_payload']) if item.get('recipe_payload') else None,
                    created_at=item['created_at']
                )
                for item in items
            ]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/user/favorites")
    @app.post("/api/favorites")
    async def add_user_favorite(
        payload: dict = Body(...),
        current_user = Depends(get_current_user)
    ):
        """Ajouter un favori"""
        try:
            favorite = FavoriteCreate(**payload)
            user_supabase = require_user_client(current_user)

            payload = {
                'user_id': current_user["id"],
                'predicted_dish': favorite.predicted_dish,
                'confidence': float(favorite.confidence),
                'top_predictions': [p.dict() for p in favorite.top_predictions],
                'servings': favorite.servings,
                'recipe_payload': favorite.recipe_payload.dict() if favorite.recipe_payload else None,
            }
            user_supabase.table('favorites').insert(payload).execute()
            return {"message": "Favori ajouté"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/api/user/favorites/{favorite_id}")
    @app.delete("/api/favorites/{favorite_id}")
    async def delete_user_favorite(
        favorite_id: str,
        current_user = Depends(get_current_user)
    ):
        """Supprimer un favori"""
        try:
            user_supabase = require_user_client(current_user)

            user_supabase.table('favorites')\
                .delete()\
                .eq('id', favorite_id)\
                .eq('user_id', current_user["id"])\
                .execute()
            return {"message": "Favori supprimé"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

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

    print("Je demarre le serveur FastAPI.")
    print("API: http://localhost:8000")
    print("Docs: http://localhost:8000/docs")
    print("Interface: http://localhost:8000")
    if supabase:
        print("Authentification Supabase activee.")
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
