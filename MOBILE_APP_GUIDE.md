# Mobile application roadmap for FoodAI

This project already has a FastAPI backend and a web UI. The easiest path to mobile is to **keep FastAPI as backend** and build a native-like client that consumes the existing API.

## 1) Choose a mobile strategy

## Option A — Flutter (recommended for speed + quality)
- One codebase for iOS + Android.
- Excellent camera support (`camera`, `image_picker`).
- Good performance and smooth UI for scan history/favorites.

## Option B — React Native (Expo)
- Good choice if your team is stronger in JavaScript/TypeScript.
- Fast prototyping and easy OTA updates.

## Option C — PWA wrapper (short-term)
- Keep current web app and wrap it with Capacitor.
- Fast to ship but weaker camera/background/native integrations.

## 2) Backend-first architecture (recommended)

Reuse existing FastAPI endpoints for:
- Auth/session (or migrate to Supabase mobile SDK directly)
- Scan upload and prediction
- Recipe retrieval
- Favorites/history CRUD

Add or validate these API contracts:
- `POST /api/scan` (multipart image upload)
- `GET /api/history`
- `POST /api/favorites`
- `DELETE /api/favorites/{id}`
- `GET /api/profile` and `PUT /api/profile`


## Implemented in this repository

To accelerate a mobile client, backend route aliases are now available:
- `POST /api/scan` (alias of `/api/predict`)
- `GET /api/profile` (alias of `/api/user/profile`)
- `GET /api/history` and `DELETE /api/history/{scan_id}` (aliases of `/api/user/history...`)
- `GET /api/favorites`, `POST /api/favorites`, `DELETE /api/favorites/{favorite_id}` (aliases of `/api/user/favorites...`)

These aliases make frontend integration cleaner on mobile while preserving backward compatibility with existing web routes.

## 3) Authentication for mobile

For production mobile apps:
- Use Supabase Auth native flow with deep links.
- Store tokens in secure storage (`Keychain` iOS, `EncryptedSharedPreferences` Android).
- Avoid localStorage-style token handling.

## 4) Mobile-specific features to implement

- Camera capture + gallery picker.
- Image compression before upload (reduce latency + cost).
- Offline cache for recent scans, recipes, and favorites.
- Retry queue for failed uploads when network returns.
- Push notifications (optional): reminders and recipe suggestions.

## 5) Recommended phased delivery

### Phase 1 (MVP, 2-4 weeks)
- Login/logout
- Scan from camera/gallery
- Top prediction + recipe details
- History list
- Favorites list

### Phase 2 (2-3 weeks)
- Profile/preferences editing
- Better error states and loading UX
- Basic analytics/crash reporting

### Phase 3 (2-4 weeks)
- Offline mode + background sync
- Push notifications
- Performance optimizations

## 6) Practical implementation checklist

1. Freeze and document API responses from FastAPI.
2. Add OpenAPI-driven client generation (optional but useful).
3. Build mobile design system (buttons/cards/loading/error).
4. Implement auth + secure token storage.
5. Implement scan flow with image compression.
6. Add robust error handling for network/model failures.
7. Add telemetry (Sentry/Firebase Crashlytics + analytics).
8. Set up CI/CD for mobile builds.

## 7) Suggested stack

- **Frontend mobile:** Flutter
- **State management:** Riverpod
- **Networking:** Dio
- **Auth:** Supabase SDK
- **Storage:** Hive/Isar + secure storage for tokens
- **Crash monitoring:** Firebase Crashlytics or Sentry

## 8) Risks and mitigations

- Large image upload latency -> compress to max width (e.g., 1024px).
- Auth complexity with Google + Supabase -> validate redirect URIs early.
- Model response time -> show progress and allow cancel/retry.
- API changes breaking app -> version endpoints (`/v1/...`) before release.

## 9) If you want the fastest start this week

1. Build a Flutter app shell with 4 tabs: Scan, History, Favorites, Profile.
2. Connect only `scan + history` APIs first.
3. Release an internal alpha to test real-world camera/upload flows.
4. Iterate on UX and prediction confidence display.

---

If needed, the next step is to create a concrete Flutter project skeleton (`lib/` folder structure, API client, auth guard, and first scan screen) mapped to your current FastAPI routes.


## 10) Flutter app skeleton delivered

A practical Flutter MVP has been added under `mobile_app/` with:
- 4 tabs: Scan, History, Favorites, Profile
- API integration with existing backend aliases (`/api/scan`, `/api/history`, `/api/favorites`, `/api/profile`)
- Camera/gallery scan flow (`image_picker`)
- Dark theme aligned with the web palette (`app/web/static/css/app.css`)

Run it:
```bash
cd mobile_app
flutter pub get
flutter run
```
