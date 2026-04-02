# Open Conta

## Purpose

Web application for SAT (Mexico tax authority) payment reconciliation. Compares CUOTAS_MEXICO files against Base SAT Mexico files to identify:

- **Pagos Faltantes** — in CUOTAS but not in SAT
- **Pagos de Mas** — in SAT but not in CUOTAS
- **Pagos Completos** — exact matches between both systems

Across three payment channels: **Aliados**, **Oxxo**, **Paynet**.

## Architecture

- **Backend:** Django 6.0 + Django REST Framework
- **Frontend:** React 19 + Vite 8 (integrated via django-vite)
- **Database:** Supabase (PostgreSQL)
- **Auth:** Supabase Auth (frontend login) + JWT verification (backend)
- **Deployment:** Vercel

## Directory Structure

```
open-conta/
├── manage.py                   # Django entry point
├── config/                     # Django project settings
│   ├── settings.py             # DRF, CORS, django-vite, Supabase
│   ├── urls.py                 # API routes + SPA catch-all
│   ├── authentication.py       # Supabase JWT verification for DRF
│   └── permissions.py          # IsAdmin, IsAdminOrReadOnly
├── reconciliacion/             # Django app
│   ├── models.py               # Periodo, CuotaMexico, PagoSAT, ResultadoReconciliacion
│   ├── serializers.py          # DRF serializers
│   ├── views.py                # API endpoints
│   ├── urls.py                 # /api/periodos/, /api/reconciliacion/*
│   ├── services.py             # Core reconciliation logic (from reconciliacion_sat.py)
│   └── admin.py                # Django admin registration
├── frontend/                   # React + Vite (source code)
│   ├── src/
│   │   ├── App.jsx             # Router with auth-protected routes
│   │   ├── lib/supabase.js     # Supabase client
│   │   ├── api/axios.js        # Axios with JWT interceptor
│   │   ├── contexts/AuthContext.jsx
│   │   ├── components/         # Layout, ProtectedRoute
│   │   └── pages/              # Login, Dashboard, Upload, Resultados
│   ├── vite.config.js          # Build outputs to ../static/
│   └── package.json
├── templates/
│   └── index.html              # Django template loading React SPA via django_vite
├── static/                     # Vite build output (generated, do not edit)
├── reconciliacion_sat.py       # Original standalone script (reference only)
├── requirements.txt            # Python dependencies
└── .env.example                # Required environment variables
```

## Development

### Prerequisites

- Python 3.13 (via pyenv)
- Node.js v24+ and npm
- Supabase project (for DB and auth)

### Setup

```bash
# Activate environment
source .env.sh

# Copy and fill environment variables
cp .env.example .env
cp frontend/.env.example frontend/.env

# Install Python deps (venv already at .venv/)
pip install -r requirements.txt

# Install frontend deps
cd frontend && npm install && cd ..

# Run migrations
python manage.py migrate
```

### Run dev servers

```bash
# Terminal 1 — Django backend (port 8000)
source .env.sh
python manage.py runserver

# Terminal 2 — Vite dev server with HMR (port 5173)
cd frontend && npm run dev
```

Visit http://localhost:8000 — Django serves the SPA, Vite provides hot reload.

### Build for production

```bash
cd frontend && npm run build   # outputs to static/
python manage.py collectstatic
```

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/periodos/` | any | List periods |
| POST | `/api/periodos/` | admin | Create period |
| POST | `/api/reconciliacion/upload/` | admin | Upload Excel files and run reconciliation |
| GET | `/api/reconciliacion/resultados/` | any | Query results (filters: periodo, tipo, canal) |
| GET | `/api/reconciliacion/resumen/` | any | Summary totals by type and channel |

## Environment Variables

See `.env.example`. Required:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Supabase PostgreSQL connection string |
| `DJANGO_SECRET_KEY` | Django secret key |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anonymous key |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key |
| `SUPABASE_JWT_SECRET` | JWT secret from Supabase dashboard |
| `VITE_SUPABASE_URL` | Supabase URL for frontend |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon key for frontend |
| `VITE_API_URL` | Backend API URL for frontend |

## User Roles

- **admin** — Full access: upload files, run reconciliation, view results
- **usuario** — Read-only: view reconciliation results

Roles are stored in Supabase user_metadata and verified server-side via JWT.

## Key Commands

```bash
python manage.py makemigrations    # after model changes
python manage.py migrate           # apply migrations
python manage.py check             # verify Django config
cd frontend && npm run dev          # Vite dev server
cd frontend && npm run build        # production build
```
