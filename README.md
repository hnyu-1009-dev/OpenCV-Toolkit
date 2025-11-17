# OpenCV Toolkit

## Overview
OpenCV Toolkit is a bilingual (中 / EN) full-stack playground for computer-vision workflows. The repository bundles a FastAPI + Tortoise ORM backend for heavy OpenCV / Pillow processing together with a Vue 3 + Element Plus single-page workspace that lets users upload images, tune parameters, and persist results into a shared gallery.

## Repository Layout
```
OpenCV-Toolkit/
├─ backend-fastapi/OpenCV-Toolkit/   # FastAPI service, Tortoise ORM models, Aerich migrations
│  ├─ app/                           # API routers, business services, settings, DB session
│  ├─ storage/                       # Uploaded assets exposed at /media
│  └─ migrations/                    # Aerich-generated schema history
└─ frontend-vue/OpenCV-Toolkit/      # Vue 3 workspace (Vite) + Element Plus UI
   ├─ src/api                        # REST clients for Auth, Gallery, Vision features
   ├─ src/views                      # Pages: Workspace, Gallery, Profile, Auth, etc.
   └─ src/stores                     # Pinia auth store with localStorage persistence
```

## Key Features
### Vision & Gallery services (backend)
* Unified `/api/v1` router with auth, health, dashboard, and user modules keeps the API surface predictable for the SPA and future automation clients.【F:backend-fastapi/OpenCV-Toolkit/app/main.py†L24-L77】【F:backend-fastapi/OpenCV-Toolkit/app/api/router.py†L1-L11】
* Dashboard endpoints cover gallery CRUD plus advanced OpenCV operations—color-blind simulation, perspective document scan, watermark overlay, rotation, contrast, and brightness adjustments—each optionally persisting processed files back to the gallery via shared helpers.【F:backend-fastapi/OpenCV-Toolkit/app/api/v1/dashboard.py†L49-L483】
* Dedicated health, auth, and user controllers provide operational probes (`GET /health`), credential workflows (`/auth/login`, `/auth/register`), and profile retrieval/update endpoints (`/users/{id}`).【F:backend-fastapi/OpenCV-Toolkit/app/api/v1/health.py†L1-L12】【F:backend-fastapi/OpenCV-Toolkit/app/api/v1/auth.py†L1-L32】【F:backend-fastapi/OpenCV-Toolkit/app/api/v1/user.py†L1-L32】

### Frontend workspace
* The workspace view exposes tabbed tools for color-blind checks, document scanning, watermark placement, brightness/contrast tweaks, and precise rotation—all backed by draggable overlays, sliders, and upload widgets implemented with Element Plus.【F:frontend-vue/OpenCV-Toolkit/src/views/WorkspaceView.vue†L1-L200】
* Pinia-based auth state keeps JWTs and user profiles synced with localStorage while helper composables guard protected routes.【F:frontend-vue/OpenCV-Toolkit/src/stores/auth.ts†L1-L56】
* Axios service injects the `VITE_API_BASE_URL` at runtime and handles token injection plus global error messaging so the UI automatically reacts to expired sessions.【F:frontend-vue/OpenCV-Toolkit/src/services/http.ts†L1-L44】

## Tech Stack
| Layer | Technologies |
| --- | --- |
| Backend | FastAPI, Tortoise ORM, Aerich, Pillow, OpenCV, Uvicorn (Python ≥3.11).【F:backend-fastapi/OpenCV-Toolkit/pyproject.toml†L1-L27】 |
| Frontend | Vue 3 + TypeScript, Vite, Pinia, Vue Router, Element Plus (Node 20.19+/pnpm).【F:frontend-vue/OpenCV-Toolkit/package.json†L1-L38】 |
| Storage | Local `storage/` directory served at `/media` for uploaded originals and processed previews.【F:backend-fastapi/OpenCV-Toolkit/app/main.py†L43-L52】 |

## Getting Started
### 1. Backend API
1. `cd backend-fastapi/OpenCV-Toolkit`
2. Create a virtualenv (`python -m venv .venv && source .venv/bin/activate`) with Python 3.11+ and install deps: `pip install -e .`【F:backend-fastapi/OpenCV-Toolkit/pyproject.toml†L1-L16】
3. Configure the database DSN (defaults to the MySQL URI inside `app/db/session.py`). Update the `"default"` connection string or wire it to your `.env` before running migrations.【F:backend-fastapi/OpenCV-Toolkit/app/db/session.py†L7-L35】
4. Apply schema migrations with Aerich (optional but recommended): `aerich upgrade` uses the shared `TORTOISE_ORM_CONFIG`.【F:backend-fastapi/OpenCV-Toolkit/app/db/session.py†L7-L22】
5. Launch the API: `uvicorn app.main:app --reload` (or rely on the `[tool.uvicorn]` defaults in `pyproject.toml`).【F:backend-fastapi/OpenCV-Toolkit/pyproject.toml†L18-L22】
6. Verify `GET http://127.0.0.1:8000/api/v1/health` returns `{ "status": "ok" }`.【F:backend-fastapi/OpenCV-Toolkit/app/api/v1/health.py†L1-L12】

### 2. Frontend workspace
1. Install pnpm (or enable Corepack) and move into `frontend-vue/OpenCV-Toolkit`.
2. Create an `.env` file (see _Environment variables_) so the SPA knows where the API lives.
3. Install dependencies: `pnpm install`.【F:frontend-vue/OpenCV-Toolkit/package.json†L1-L38】
4. Run the dev server: `pnpm dev` (Vite will start at `http://localhost:5173`).【F:frontend-vue/OpenCV-Toolkit/package.json†L9-L15】
5. Optional scripts: `pnpm build` for production bundles, `pnpm preview` to serve a local preview, `pnpm lint` / `pnpm type-check` for quality gates.【F:frontend-vue/OpenCV-Toolkit/package.json†L9-L15】

### 3. Working with uploads
* Uploaded originals and processed images are persisted under `backend-fastapi/OpenCV-Toolkit/storage`. FastAPI automatically exposes them via `/media/...`, so the front-end can render thumbnails directly using URLs returned from any `/dashboard/vision/*` endpoint.【F:backend-fastapi/OpenCV-Toolkit/app/main.py†L43-L52】【F:backend-fastapi/OpenCV-Toolkit/app/api/v1/dashboard.py†L32-L124】

## Environment Variables
| Component | Variable | Default | Notes |
| --- | --- | --- | --- |
| Backend | `PROJECT_NAME`, `VERSION`, `API_PREFIX` | See `app/core/config.py` | Override FastAPI metadata without touching code.【F:backend-fastapi/OpenCV-Toolkit/app/core/config.py†L7-L30】 |
| Backend | `DATABASE_URL` | `sqlite://app.db` | Align this with the DSN in `app/db/session.py` when switching between SQLite/MySQL/PostgreSQL.【F:backend-fastapi/OpenCV-Toolkit/app/core/config.py†L21-L31】【F:backend-fastapi/OpenCV-Toolkit/app/db/session.py†L7-L35】 |
| Backend | `MEDIA_ROOT` | `storage` | Controls where uploads land on disk.【F:backend-fastapi/OpenCV-Toolkit/app/core/config.py†L24-L31】 |
| Backend | `BACKEND_CORS_ORIGINS` | `http://localhost:5173`, `http://127.0.0.1:5173` | Add your deployed frontend domains here for cross-origin access.【F:backend-fastapi/OpenCV-Toolkit/app/core/config.py†L27-L31】 |
| Frontend | `VITE_API_BASE_URL` | `http://127.0.0.1:8000/api/v1` | Configure the Axios base URL. Falls back to localhost when undefined.【F:frontend-vue/OpenCV-Toolkit/src/services/http.ts†L14-L44】 |

## Frequently Used Commands
| Context | Command | Purpose |
| --- | --- | --- |
| Backend | `uvicorn app.main:app --reload` | Start the API with autoreload during development.【F:backend-fastapi/OpenCV-Toolkit/pyproject.toml†L18-L22】 |
| Backend | `aerich upgrade` | Apply DB migrations stored in `migrations/`.【F:backend-fastapi/OpenCV-Toolkit/app/db/session.py†L7-L35】 |
| Frontend | `pnpm dev` | Launch the Vite dev server with HMR.【F:frontend-vue/OpenCV-Toolkit/package.json†L9-L15】 |
| Frontend | `pnpm build` | Produce optimized assets for deployment.【F:frontend-vue/OpenCV-Toolkit/package.json†L9-L15】 |
| Frontend | `pnpm lint` / `pnpm type-check` | Run ESLint and `vue-tsc` for code quality.【F:frontend-vue/OpenCV-Toolkit/package.json†L9-L15】 |

## API Surface Overview
| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/v1/health` | Simple liveness probe for load balancers / uptime checks.【F:backend-fastapi/OpenCV-Toolkit/app/api/v1/health.py†L1-L12】 |
| POST | `/api/v1/auth/login` | Authenticate by email + password and receive the token / profile bundle.【F:backend-fastapi/OpenCV-Toolkit/app/api/v1/auth.py†L1-L21】 |
| POST | `/api/v1/auth/register` | Lightweight registration returning the same payload as login.【F:backend-fastapi/OpenCV-Toolkit/app/api/v1/auth.py†L23-L32】 |
| GET / PATCH | `/api/v1/users/{user_id}` | Fetch or update personal profile data via the user service.【F:backend-fastapi/OpenCV-Toolkit/app/api/v1/user.py†L9-L32】 |
| GET | `/api/v1/dashboard/summary` | Returns aggregate counters for the workspace home tiles.【F:backend-fastapi/OpenCV-Toolkit/app/api/v1/dashboard.py†L49-L54】 |
| POST | `/api/v1/dashboard/gallery` | Persist gallery metadata when the file already exists on disk.【F:backend-fastapi/OpenCV-Toolkit/app/api/v1/dashboard.py†L56-L66】 |
| POST | `/api/v1/dashboard/gallery/upload` | Accept multipart uploads, save to disk, and create gallery entries.【F:backend-fastapi/OpenCV-Toolkit/app/api/v1/dashboard.py†L68-L86】 |
| GET | `/api/v1/dashboard/gallery/{user_id}` | Paginated gallery listing with optional date filters.【F:backend-fastapi/OpenCV-Toolkit/app/api/v1/dashboard.py†L88-L124】 |
| DELETE | `/api/v1/dashboard/gallery/{item_id}` | Remove gallery items while optionally enforcing user ownership.【F:backend-fastapi/OpenCV-Toolkit/app/api/v1/dashboard.py†L126-L139】 |
| POST | `/api/v1/dashboard/vision/color-blind` | Run color-blind simulation, optionally saving original / processed files.【F:backend-fastapi/OpenCV-Toolkit/app/api/v1/dashboard.py†L142-L203】 |
| POST | `/api/v1/dashboard/vision/document-scan` | Perspective-correct documents based on four user-selected points.【F:backend-fastapi/OpenCV-Toolkit/app/api/v1/dashboard.py†L206-L259】 |
| POST | `/api/v1/dashboard/vision/rotate` | Free-form rotation with persistent outputs when desired.【F:backend-fastapi/OpenCV-Toolkit/app/api/v1/dashboard.py†L262-L312】 |
| POST | `/api/v1/dashboard/vision/watermark` | Overlay an uploaded watermark using normalized coordinates.【F:backend-fastapi/OpenCV-Toolkit/app/api/v1/dashboard.py†L315-L377】 |
| POST | `/api/v1/dashboard/vision/contrast` | Adjust contrast by a supplied factor (−1.0 to 1.0 recommended).【F:backend-fastapi/OpenCV-Toolkit/app/api/v1/dashboard.py†L380-L430】 |
| POST | `/api/v1/dashboard/vision/brightness` | Brightness offset to lighten or darken frames uniformly.【F:backend-fastapi/OpenCV-Toolkit/app/api/v1/dashboard.py†L433-L483】 |

---
Need something else? Open an issue or start a discussion so we can expand the toolkit (OCR, batch pipelines, etc.) together!
