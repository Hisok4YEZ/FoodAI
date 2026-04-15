# FoodAI Mobile (Flutter)

Application mobile Flutter pour iOS/Android, branchée sur le backend FastAPI existant (`app/web/server.py`).

## Objectif
- Ne pas casser l'architecture actuelle.
- Réutiliser les routes backend existantes + alias mobile:
  - `POST /api/scan`
  - `GET /api/history`
  - `GET /api/favorites`
  - `GET /api/profile`

## Lancer le projet
```bash
cd mobile_app
flutter pub get
flutter run
```

## Configuration backend
Par défaut l'app appelle `http://10.0.2.2:8000` (Android emulator).

Tu peux changer l'URL dans `lib/core/config.dart`.

## Structure
- `lib/main.dart`: bootstrap app + providers
- `lib/theme/app_theme.dart`: thème visuel inspiré du site web
- `lib/services/api_service.dart`: appels HTTP vers FastAPI
- `lib/services/auth_service.dart`: connexion Google/Supabase
- `lib/screens/`: écrans Scan / History / Favorites / Profile

## Notes
- Auth Google/Supabase mobile est câblée, mais il faut fournir les `dart-define` Supabase au lancement.
- Le flow de scan (camera + galerie) est implémenté avec `image_picker`.
