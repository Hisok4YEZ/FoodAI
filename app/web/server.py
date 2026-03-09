from __future__ import annotations

import sys
from pathlib import Path
import argparse
import os
import re
import subprocess
import threading
from datetime import datetime, timezone
from uuid import uuid4
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from dotenv import load_dotenv
import requests
import math
import asyncio

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
    """Lance le backend web FastAPI avec Supabase"""
    if not FASTAPI_AVAILABLE:
        print("❌ FastAPI n'est pas installé. Installez-le avec:")
        print("   pip install fastapi uvicorn python-multipart pydantic")
        sys.exit(1)
    
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

    if not SUPABASE_AVAILABLE:
        print("⚠️ Supabase n'est pas installé. Les fonctionnalités d'authentification seront désactivées.")
        print("   Pour activer : pip install supabase")
        supabase: Optional[Client] = None
        supabase_admin: Optional[Client] = None
    else:
        if SUPABASE_URL and SUPABASE_KEY:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("✅ Supabase connecté")
            if SUPABASE_SERVICE_KEY:
                supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
                print("✅ Supabase service role activé pour endpoints admin")
            else:
                supabase_admin = supabase
                print("⚠️ SUPABASE_SERVICE_ROLE_KEY absent: endpoints admin en mode limité")
        else:
            print("⚠️ Variables SUPABASE_URL et SUPABASE_ANON_KEY non définies")
            print("   Les fonctionnalités d'authentification seront désactivées")
            supabase = None
            supabase_admin = None
    
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
    print("🔄 Chargement de la base de recettes...")
    try:
        db = RecipeDB.load()
        print("✅ Base recettes chargée")
    except Exception as e:
        print(f"❌ Erreur chargement recettes: {e}")
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
                print("🔄 Chargement du modèle IA (lazy load)...")
                from app.ml.predictor import FoodPredictor
                predictor = FoodPredictor(model_path="models/model_food.pth")
                print("✅ Modèle IA chargé")
                return predictor
            except Exception as e:
                predictor_error = f"Chargement modèle impossible: {e}"
                print(f"❌ {predictor_error}")
                raise RuntimeError(predictor_error)

    retrain_state: Dict[str, Any] = {
        "status": "idle",
        "job_id": None,
        "started_at": None,
        "finished_at": None,
        "message": None,
        "downloaded_images": 0,
        "candidates_count": 0,
        "batch_dir": None,
        "last_stdout_tail": None,
        "last_stderr_tail": None,
    }
    retrain_lock = threading.Lock()

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
        recipe_payload: Optional[RecipeResponse] = None
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

    class CandidateRecipe(BaseModel):
        name: str
        servings: int
        ingredients: List[str]
        steps: List[str]

    class CandidateIngest(BaseModel):
        source_keyword: Optional[str] = None
        dish_name: str
        servings: int = 2
        image_url: Optional[str] = None
        notes: Optional[str] = None
        recipe: Optional[CandidateRecipe] = None
        insert_known: bool = False
        auto_approve: bool = False

    class CandidateBatchIngest(BaseModel):
        candidates: List[CandidateIngest]

    class CandidateUpdate(BaseModel):
        status: Optional[str] = None
        added_to_training: Optional[bool] = None
        admin_note: Optional[str] = None

    class IncrementalRetrainRequest(BaseModel):
        limit_candidates: int = 50
        epochs: int = 2
        replay_per_class: int = 20

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

    def get_admin_client():
        return supabase_admin if supabase_admin else supabase

    def dish_exists_in_catalog(dish_name: str) -> bool:
        if not db:
            return False
        dish_name_norm = dish_name.strip().lower()
        if not dish_name_norm:
            return False
        for dish in db.dishes:
            if dish.name.strip().lower() == dish_name_norm or dish.id.strip().lower() == dish_name_norm:
                return True
        return False

    def normalize_label_name(name: str) -> str:
        label = name.strip().lower()
        label = re.sub(r"[^a-z0-9]+", "_", label)
        label = label.strip("_")
        return label or "unknown_dish"

    def safe_image_extension(image_url: str) -> str:
        ext = Path(urlparse(image_url).path).suffix.lower()
        return ext if ext in {".jpg", ".jpeg", ".png", ".webp", ".bmp"} else ".jpg"

    def download_image_to_path(image_url: str, dest_path: Path) -> bool:
        try:
            req = Request(
                image_url,
                headers={"User-Agent": "Mozilla/5.0 (FoodAI retrain bot)"},
            )
            with urlopen(req, timeout=20) as response:
                content_type = (response.headers.get("Content-Type") or "").lower()
                if "image" not in content_type:
                    return False
                data = response.read()
            if not data or len(data) < 1024:
                return False
            dest_path.write_bytes(data)
            return True
        except Exception:
            return False

    def update_retrain_state(**kwargs):
        with retrain_lock:
            retrain_state.update(kwargs)

    def list_approved_candidates_for_retrain(limit_candidates: int):
        admin_client = get_admin_client()
        if not admin_client:
            raise HTTPException(status_code=503, detail="Supabase non configuré")
        query = (
            admin_client.table("dish_candidates")
            .select("*")
            .eq("status", "approved")
            .eq("added_to_training", False)
            .order("created_at", desc=False)
            .limit(limit_candidates)
        )
        result = query.execute()
        return result.data or []

    def build_incremental_batch(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        batch_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        batch_dir = PROJECT_ROOT / "data" / "auto_batches" / batch_id
        batch_dir.mkdir(parents=True, exist_ok=True)

        accepted_candidate_ids: List[str] = []
        downloaded_count = 0
        class_counts: Dict[str, int] = {}

        for candidate in candidates:
            dish_name = (candidate.get("dish_name") or "").strip()
            image_url = (candidate.get("image_url") or "").strip()
            candidate_id = candidate.get("id")
            if not dish_name or not image_url or not candidate_id:
                continue

            class_name = normalize_label_name(dish_name)
            class_dir = batch_dir / class_name
            class_dir.mkdir(parents=True, exist_ok=True)

            ext = safe_image_extension(image_url)
            image_path = class_dir / f"{candidate_id}{ext}"

            if download_image_to_path(image_url, image_path):
                downloaded_count += 1
                class_counts[class_name] = class_counts.get(class_name, 0) + 1
                accepted_candidate_ids.append(candidate_id)

        return {
            "batch_dir": str(batch_dir),
            "batch_id": batch_id,
            "downloaded_count": downloaded_count,
            "candidate_ids": accepted_candidate_ids,
            "class_counts": class_counts,
        }

    def mark_candidates_as_trained(candidate_ids: List[str], success: bool, note: Optional[str] = None):
        admin_client = get_admin_client()
        if not admin_client:
            return
        for candidate_id in candidate_ids:
            payload: Dict[str, Any] = {}
            if success:
                payload.update({"added_to_training": True, "status": "trained"})
            if note:
                payload["admin_note"] = note
            if payload:
                try:
                    admin_client.table("dish_candidates").update(payload).eq("id", candidate_id).execute()
                except Exception:
                    pass

    def run_incremental_retrain_worker(job_id: str, batch_dir: str, candidate_ids: List[str], epochs: int, replay_per_class: int):
        update_retrain_state(
            status="running",
            job_id=job_id,
            started_at=datetime.now(timezone.utc).isoformat(),
            finished_at=None,
            message="Retrain incrémental en cours",
            last_stdout_tail=None,
            last_stderr_tail=None,
        )

        cmd = [
            sys.executable,
            "-m",
            "app.ml.retrain_incremental",
            "--batch-dir",
            batch_dir,
            "--base-model",
            "models/model_food.pth",
            "--out",
            "models/model_food.pth",
            "--data",
            "data/food",
            "--epochs",
            str(epochs),
            "--replay-per-class",
            str(replay_per_class),
        ]

        try:
            proc = subprocess.run(
                cmd,
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                check=False,
            )
            stdout_tail = (proc.stdout or "")[-2000:]
            stderr_tail = (proc.stderr or "")[-2000:]
            if proc.returncode == 0:
                mark_candidates_as_trained(candidate_ids, success=True, note="Auto trained")
                update_retrain_state(
                    status="completed",
                    finished_at=datetime.now(timezone.utc).isoformat(),
                    message="Retrain terminé avec succès",
                    last_stdout_tail=stdout_tail,
                    last_stderr_tail=stderr_tail,
                )
            else:
                update_retrain_state(
                    status="failed",
                    finished_at=datetime.now(timezone.utc).isoformat(),
                    message=f"Retrain échoué (code {proc.returncode})",
                    last_stdout_tail=stdout_tail,
                    last_stderr_tail=stderr_tail,
                )
        except Exception as e:
            update_retrain_state(
                status="failed",
                finished_at=datetime.now(timezone.utc).isoformat(),
                message=f"Erreur retrain: {e}",
                last_stdout_tail=None,
                last_stderr_tail=None,
            )

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
            print(f"Erreur auth: {e}")
            return None

    async def require_admin(x_admin_token: str = Header(None, alias="X-Admin-Token")):
        if not ADMIN_TOKEN:
            raise HTTPException(status_code=503, detail="ADMIN_TOKEN non configuré")
        if not x_admin_token or x_admin_token != ADMIN_TOKEN:
            raise HTTPException(status_code=401, detail="Non autorisé (admin token)")
        return True

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

    @app.get("/admin")
    async def admin_page():
        return HTMLResponse(content=render_html_template("admin.html"))

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

    @app.post("/api/predict", response_model=FullPredictionResponse)
    async def predict(
        file: UploadFile = File(...),
        servings: int = 2,
        min_confidence: float = 0.70,
        current_user = Depends(get_current_user)
    ):
        """Prédire le plat à partir d'une image et retourner la recette"""
        print(f"📸 Nouvelle prédiction - Fichier: {file.filename}, Portions: {servings}, Seuil: {min_confidence}")
        
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
            
            print(f"🔍 Analyse de l'image: {tmp_path}")
            
            # Prédiction
            predictions = active_predictor.predict_topk(tmp_path, k=3)
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
                                print(f"⚠️ Erreur upload image (consentement actif): {upload_error}")

                        user_supabase.table('scan_history').insert({
                            'user_id': current_user["id"],
                            'image_url': image_url,
                            'predicted_dish': best.label,
                            'confidence': float(best.confidence),
                            'top_predictions': [{'label': p.label, 'confidence': p.confidence} for p in predictions_data],
                            'servings': servings,
                            'recipe_payload': recipe_data.model_dump() if recipe_data else None
                        }).execute()
                        print(f"💾 Scan sauvegardé pour l'utilisateur {current_user['email']}")
                except Exception as e:
                    print(f"⚠️ Erreur sauvegarde historique: {e}")
            
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

    # ============================================
    # ENDPOINTS UTILISATEURS
    # ============================================

    @app.get("/api/user/profile", response_model=UserProfile)
    async def get_user_profile(current_user = Depends(get_current_user)):
        """Obtenir le profil de l'utilisateur connecté"""
        if not current_user or not supabase:
            raise HTTPException(status_code=401, detail="Non authentifié")
        
        try:
            user_supabase = get_user_scoped_client(current_user["token"])
            if not user_supabase:
                raise HTTPException(status_code=500, detail="Client Supabase indisponible")
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
        if not current_user or not supabase:
            raise HTTPException(status_code=401, detail="Non authentifié")
        
        try:
            updates = UserUpdate(**payload)
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=e.errors())
        
        try:
            update_data = updates.dict(exclude_unset=True)
            if not update_data:
                raise HTTPException(status_code=400, detail="Aucune donnée à mettre à jour")
            
            user_supabase = get_user_scoped_client(current_user["token"])
            if not user_supabase:
                raise HTTPException(status_code=500, detail="Client Supabase indisponible")
            user_supabase.table('users').update(update_data).eq('id', current_user["id"]).execute()
            return {"message": "Profil mis à jour avec succès"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/user/history", response_model=List[ScanHistoryItem])
    async def get_user_history(
        limit: int = 50,
        current_user = Depends(get_current_user)
    ):
        """Obtenir l'historique des scans de l'utilisateur"""
        if not current_user or not supabase:
            raise HTTPException(status_code=401, detail="Non authentifié")
        
        try:
            user_supabase = get_user_scoped_client(current_user["token"])
            if not user_supabase:
                raise HTTPException(status_code=500, detail="Client Supabase indisponible")
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
                    recipe_payload=RecipeResponse(**item['recipe_payload']) if item.get('recipe_payload') else None,
                    created_at=item['created_at']
                )
                for item in result.data
            ]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/api/user/history/{scan_id}")
    async def delete_scan_from_history(
        scan_id: str,
        current_user = Depends(get_current_user)
    ):
        """Supprimer un scan de l'historique"""
        if not current_user or not supabase:
            raise HTTPException(status_code=401, detail="Non authentifié")
        
        try:
            user_supabase = get_user_scoped_client(current_user["token"])
            if not user_supabase:
                raise HTTPException(status_code=500, detail="Client Supabase indisponible")
            user_supabase.table('scan_history')\
                .delete()\
                .eq('id', scan_id)\
                .eq('user_id', current_user["id"])\
                .execute()
            return {"message": "Scan supprimé de l'historique"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/user/favorites", response_model=List[FavoriteItem])
    async def get_user_favorites(
        limit: int = 100,
        current_user = Depends(get_current_user)
    ):
        """Obtenir les favoris de l'utilisateur"""
        if not current_user or not supabase:
            raise HTTPException(status_code=401, detail="Non authentifié")

        try:
            user_supabase = get_user_scoped_client(current_user["token"])
            if not user_supabase:
                raise HTTPException(status_code=500, detail="Client Supabase indisponible")

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
    async def add_user_favorite(
        payload: dict = Body(...),
        current_user = Depends(get_current_user)
    ):
        """Ajouter un favori"""
        if not current_user or not supabase:
            raise HTTPException(status_code=401, detail="Non authentifié")

        try:
            favorite = FavoriteCreate(**payload)
            user_supabase = get_user_scoped_client(current_user["token"])
            if not user_supabase:
                raise HTTPException(status_code=500, detail="Client Supabase indisponible")

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
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/api/user/favorites/{favorite_id}")
    async def delete_user_favorite(
        favorite_id: str,
        current_user = Depends(get_current_user)
    ):
        """Supprimer un favori"""
        if not current_user or not supabase:
            raise HTTPException(status_code=401, detail="Non authentifié")

        try:
            user_supabase = get_user_scoped_client(current_user["token"])
            if not user_supabase:
                raise HTTPException(status_code=500, detail="Client Supabase indisponible")

            user_supabase.table('favorites')\
                .delete()\
                .eq('id', favorite_id)\
                .eq('user_id', current_user["id"])\
                .execute()
            return {"message": "Favori supprimé"}
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

    # ============================================
    # ENDPOINTS ADMIN
    # ============================================

    @app.get("/api/supermarkets/nearby")
    async def get_nearby_supermarkets(lat: float, lon: float):
        """Trouve le supermarché supporté le plus proche via l'API Overpass"""
        radius = 5000  # 5km de rayon
        overpass_url = "http://overpass-api.de/api/interpreter"
        overpass_query = f"""
        [out:json];
        (
          node["shop"="supermarket"](around:{radius},{lat},{lon});
          way["shop"="supermarket"](around:{radius},{lat},{lon});
          relation["shop"="supermarket"](around:{radius},{lat},{lon});
        );
        out center;
        """
        try:
            # run requests in thread to avoid blocking event loop
            response = await asyncio.to_thread(requests.post, overpass_url, data={'data': overpass_query}, timeout=10)
            data = response.json()
            
            supported_chains = {
                "carrefour": "https://www.carrefour.fr/s?q=",
                "auchan": "https://www.auchan.fr/recherche?text=",
                "leclerc": "https://www.leclercdrive.fr/recherche.aspx?q=",
                "e.leclerc": "https://www.leclercdrive.fr/recherche.aspx?q=",
                "monoprix": "https://www.monoprix.fr/courses/recherche?q=",
                "intermarche": "https://www.intermarche.com/recherche/",
                "intermarché": "https://www.intermarche.com/recherche/",
                "super u": "https://www.coursesu.com/recherche?q=",
                "hyper u": "https://www.coursesu.com/recherche?q=",
                "u express": "https://www.coursesu.com/recherche?q=",
                "casino": "https://www.casinosupermarches.fr/m/rechercher-un-produit?q=",
                "franprix": "https://www.franprix.fr/courses/recherche?q=",
                "lidl": "https://www.lidl.fr/q/search?s=",
                "aldi": "https://www.aldi.fr/resultats-de-recherche.html?query=",
                "cora": "https://www.cora.fr/recherche?q=",
                "match": "https://www.supermarchesmatch.fr/fr/recherche?q=",
            }
            
            print(f"🌍 Recherche Overpass à ({lat}, {lon}) - rayon {radius}m")
            print(f"📦 Résultats Overpass: {len(data.get('elements', []))} éléments trouvés")
            
            closest_supermarket = None
            min_distance = float('inf')
            search_url_base = None
            
            for element in data.get('elements', []):
                tags = element.get('tags', {})
                name = tags.get('name', '')
                if not name:
                    continue
                name_lower = name.lower()
                
                matched_chain = None
                matched_url = None
                for chain, url in supported_chains.items():
                    if chain in name_lower:
                        matched_chain = chain
                        matched_url = url
                        break
                        
                if matched_chain:
                    elem_lat = element.get('lat') or element.get('center', {}).get('lat')
                    elem_lon = element.get('lon') or element.get('center', {}).get('lon')
                    
                    if elem_lat and elem_lon:
                        # Haversine-like approximation for small distances
                        dx = (lon - elem_lon) * 40000 * math.cos((lat + elem_lat) * math.pi / 360) / 360
                        dy = (lat - elem_lat) * 40000 / 360
                        dist = math.sqrt(dx * dx + dy * dy)
                        
                        if dist < min_distance:
                            min_distance = dist
                            closest_supermarket = name  # Use original name with correct casing
                            search_url_base = matched_url
                            
            if closest_supermarket:
                print(f"✅ Supermarché trouvé: {closest_supermarket} à {min_distance:.2f}km")
                return {
                    "found": True,
                    "name": closest_supermarket,
                    "distance_km": round(min_distance, 2),
                    "search_url_base": search_url_base
                }
            else:
                print("❌ Aucun supermarché supporté trouvé.")
                if data.get('elements'):
                    noms = [e.get('tags', {}).get('name') for e in data['elements'][:5]]
                    print(f"   (Supermarchés vus mais non supportés: {noms})")
                return {
                    "found": False,
                    "name": "Google Shopping (Aucun grand supermarché très proche trouvé)",
                    "distance_km": None,
                    "search_url_base": "https://www.google.fr/search?tbm=shop&q="
                }
        except Exception as e:
            print(f"Erreur appel à l'API Overpass: {e}")
            return {
                "found": False,
                "name": "Recherche générique (erreur localisation)",
                "distance_km": None,
                "search_url_base": "https://www.google.fr/search?tbm=shop&q="
            }

    @app.post("/api/admin/candidates/ingest")
    async def ingest_candidate(
        payload: CandidateIngest,
        _admin_ok = Depends(require_admin)
    ):
        """Ingestion d'un candidat plat (image + recette proposée)."""
        admin_client = get_admin_client()
        if not admin_client:
            raise HTTPException(status_code=503, detail="Supabase non configuré")

        dish_name = payload.dish_name.strip()
        if not dish_name:
            raise HTTPException(status_code=400, detail="dish_name requis")

        is_new = not dish_exists_in_catalog(dish_name)
        if not is_new and not payload.insert_known:
            return {
                "message": "Plat déjà connu: candidat ignoré",
                "is_new_dish": False,
                "candidate": None,
            }

        data = {
            "dish_name": dish_name,
            "source_keyword": payload.source_keyword,
            "servings": payload.servings,
            "image_url": payload.image_url,
            "notes": payload.notes,
            "recipe_payload": payload.recipe.model_dump() if payload.recipe else None,
            "is_new_dish": is_new,
            "status": "approved" if payload.auto_approve else "pending",
            "added_to_training": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            result = admin_client.table("dish_candidates").insert(data).execute()
            return {"message": "Candidate ajouté", "is_new_dish": is_new, "candidate": (result.data or [None])[0]}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/admin/candidates/ingest/batch")
    async def ingest_candidates_batch(
        payload: CandidateBatchIngest,
        _admin_ok = Depends(require_admin)
    ):
        """Ingestion batch pour plusieurs candidats d'un coup."""
        admin_client = get_admin_client()
        if not admin_client:
            raise HTTPException(status_code=503, detail="Supabase non configuré")

        rows: List[Dict[str, Any]] = []
        skipped_invalid = 0
        skipped_known = 0

        for candidate in payload.candidates:
            dish_name = candidate.dish_name.strip()
            if not dish_name:
                skipped_invalid += 1
                continue

            is_new = not dish_exists_in_catalog(dish_name)
            if not is_new and not candidate.insert_known:
                skipped_known += 1
                continue

            rows.append({
                "dish_name": dish_name,
                "source_keyword": candidate.source_keyword,
                "servings": candidate.servings,
                "image_url": candidate.image_url,
                "notes": candidate.notes,
                "recipe_payload": candidate.recipe.model_dump() if candidate.recipe else None,
                "is_new_dish": is_new,
                "status": "approved" if candidate.auto_approve else "pending",
                "added_to_training": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })

        if not rows:
            return {
                "message": "Aucun candidat inséré",
                "inserted_count": 0,
                "skipped_invalid": skipped_invalid,
                "skipped_known": skipped_known,
            }

        try:
            result = admin_client.table("dish_candidates").insert(rows).execute()
            inserted = result.data or []
            return {
                "message": "Batch candidats inséré",
                "inserted_count": len(inserted),
                "skipped_invalid": skipped_invalid,
                "skipped_known": skipped_known,
                "candidates": inserted,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/admin/candidates")
    async def list_admin_candidates(
        status: Optional[str] = None,
        limit: int = 200,
        _admin_ok = Depends(require_admin)
    ):
        admin_client = get_admin_client()
        if not admin_client:
            raise HTTPException(status_code=503, detail="Supabase non configuré")

        try:
            query = admin_client.table("dish_candidates").select("*").order("created_at", desc=True).limit(limit)
            if status:
                query = query.eq("status", status)
            result = query.execute()
            return result.data or []
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.patch("/api/admin/candidates/{candidate_id}")
    async def update_admin_candidate(
        candidate_id: str,
        updates: CandidateUpdate = Body(...),
        _admin_ok = Depends(require_admin)
    ):
        admin_client = get_admin_client()
        if not admin_client:
            raise HTTPException(status_code=503, detail="Supabase non configuré")

        update_data = updates.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="Aucune donnée à mettre à jour")

        try:
            result = admin_client.table("dish_candidates").update(update_data).eq("id", candidate_id).execute()
            return {"message": "Candidate mis à jour", "candidate": (result.data or [None])[0]}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/admin/retrain/incremental")
    async def trigger_incremental_retrain(
        payload: IncrementalRetrainRequest = Body(...),
        _admin_ok = Depends(require_admin),
    ):
        with retrain_lock:
            if retrain_state.get("status") == "running":
                raise HTTPException(status_code=409, detail="Un retrain est déjà en cours")

        limit_candidates = max(1, min(payload.limit_candidates, 500))
        epochs = max(1, min(payload.epochs, 20))
        replay_per_class = max(0, min(payload.replay_per_class, 200))

        candidates = list_approved_candidates_for_retrain(limit_candidates)
        if not candidates:
            raise HTTPException(status_code=400, detail="Aucun candidat approuvé disponible")

        batch_info = build_incremental_batch(candidates)
        if batch_info["downloaded_count"] <= 0:
            raise HTTPException(status_code=400, detail="Aucune image exploitable téléchargée depuis les candidats")

        job_id = datetime.now(timezone.utc).strftime("job_%Y%m%d_%H%M%S")
        update_retrain_state(
            status="queued",
            job_id=job_id,
            started_at=None,
            finished_at=None,
            message="Retrain en file d'attente",
            downloaded_images=batch_info["downloaded_count"],
            candidates_count=len(batch_info["candidate_ids"]),
            batch_dir=batch_info["batch_dir"],
            last_stdout_tail=None,
            last_stderr_tail=None,
        )

        worker = threading.Thread(
            target=run_incremental_retrain_worker,
            args=(
                job_id,
                batch_info["batch_dir"],
                batch_info["candidate_ids"],
                epochs,
                replay_per_class,
            ),
            daemon=True,
        )
        worker.start()

        return {
            "message": "Retrain incrémental lancé",
            "job_id": job_id,
            "downloaded_images": batch_info["downloaded_count"],
            "candidates_count": len(batch_info["candidate_ids"]),
            "batch_dir": batch_info["batch_dir"],
            "class_counts": batch_info["class_counts"],
        }

    @app.get("/api/admin/retrain/status")
    async def get_incremental_retrain_status(_admin_ok = Depends(require_admin)):
        with retrain_lock:
            return dict(retrain_state)

    print("🚀 Démarrage du serveur FastAPI...")
    print("📍 L'API sera accessible sur : http://localhost:8080")
    print("📚 Documentation interactive : http://localhost:8080/docs")
    print("🌐 Interface web : http://localhost:8080")
    if supabase:
        print("🔐 Authentification Supabase activée")
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=False)


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
