# ALDST - AI Learning Disability Support Tool

ALDST is a full-stack learning assistant for students with ADHD and dyslexia. It accepts pasted text or text-based PDFs and creates simplified notes, flashcards, quiz questions, focus-mode cards, translation-ready text, browser audio playback, history, settings, analytics, and exports.

## Tech Stack

- Frontend: React, Vite, Tailwind CSS
- Backend: FastAPI, SQLAlchemy, JWT authentication
- Database: SQLite locally, PostgreSQL/Supabase-ready for deployment
- AI layer: Groq `llama-3.1-8b-instant` integration, provider-based translation, and local fallback
- Deployment target: Vercel frontend, Render/Railway backend

## Local Setup

Use two terminals: one for the backend and one for the frontend.

### Backend Setup

```powershell
cd "D:\4th Semester\SE\backend"
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

Backend URL:

```text
http://127.0.0.1:8010
```

API docs:

```text
http://127.0.0.1:8010/docs
```

Production-style backend command:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend Setup

```powershell
cd "D:\4th Semester\SE\frontend"
npm install
copy .env.example .env
npm run dev
```

Frontend URL:

```text
http://127.0.0.1:5173
```

Your `frontend/.env` should contain:

```env
VITE_API_URL=http://127.0.0.1:8010/api
```

## Environment Variables

Backend `.env`:

```env
DATABASE_URL=sqlite:///./aldst.db
SECRET_KEY=change-this-secret-key-before-deployment
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
FRONTEND_ORIGIN=http://localhost:5173,http://127.0.0.1:5173
HF_API_TOKEN=
HF_MODEL=Qwen/Qwen2.5-7B-Instruct
HF_TTS_MODEL=facebook/mms-tts-eng
USE_HF_AI=false
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=llama-3.1-8b-instant
TRANSLATION_PROVIDER=groq
```

## Translation Setup

ALDST uses a provider-based translation service. It does not use DeepL, Google Translate, Azure Translator, or any dedicated translation provider that requires billing details, card information, or a paid translation trial.

### Translation Modes

- Groq mode: recommended for deployment. Uses the existing `GROQ_API_KEY` already used by the AI study-note generator.
- Argos mode: optional local/offline mode. Useful for privacy-focused local demos after installing local language packages.
- Disabled mode: returns a clear setup message when translation is not configured.

Recommended deployment configuration:

```env
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=llama-3.1-8b-instant
TRANSLATION_PROVIDER=groq
```

If `TRANSLATION_PROVIDER` is not set, ALDST automatically uses Groq when `GROQ_API_KEY` exists. If no valid provider is configured, the app shows:

```text
Translation provider is not configured. Add GROQ_API_KEY or enable local Argos translation.
```

The Translate button sends generated study material only: title, simplified notes, short summary, key points, flashcards, and quiz questions. It does not translate raw PDF/input text.

Supported targets:

```text
Urdu
Arabic
French
Spanish
German
```

### Optional Argos Mode

Argos Translate is optional for local/offline translation. For deployment, Groq is recommended because it avoids large model installation on hosted servers.

To use Argos locally:

```env
TRANSLATION_PROVIDER=argos
```

Then install one local language package:

```powershell
cd "D:\4th Semester\SE\backend"
python scripts\install_argos_packages.py french
```

Or install every supported local package:

```powershell
cd "D:\4th Semester\SE\backend"
python scripts\install_argos_packages.py all
```

If an Argos package is missing, the app shows:

```text
Translation model for this language is not installed. Please install the language package or choose another language.
```

Frontend `.env`:

```env
VITE_API_URL=http://127.0.0.1:8010/api
```

## Demo Test Flow

1. Sign up.
2. Log in.
3. Open Dashboard.
4. Start a new study session.
5. Paste text or upload a text-based PDF.
6. Generate notes and flashcards.
7. Open Focus Mode and complete the cards.
8. Choose a target language and use Translate with Groq mode or optional local Argos mode.
9. Generate browser audio and use play/stop controls.
10. Open History.
11. Export notes as PDF, Markdown, or TXT.
12. Update Settings.
13. Log out.

## Quality Checks

Frontend build:

```powershell
cd "D:\4th Semester\SE\frontend"
npm run build
```

Backend compile check:

```powershell
cd "D:\4th Semester\SE\backend"
python -m compileall app
```

FastAPI import check:

```powershell
cd "D:\4th Semester\SE\backend"
python -c "from app.main import app; print(app.title, len(app.routes))"
```

Expected output includes:

```text
ALDST API 21
```

## Vercel Frontend Deployment

Use `frontend` as the Vercel project root.

Build command:

```bash
npm run build
```

Output directory:

```text
dist
```

Set this Vercel environment variable:

```env
VITE_API_URL=https://your-backend-url/api
```

## Render/Railway Backend Deployment

Use `backend` as the backend service root.

Install command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

If your platform provides a `$PORT` variable, use:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Set backend environment variables:

```env
DATABASE_URL=sqlite:///./aldst.db
SECRET_KEY=use-a-long-random-secret
FRONTEND_ORIGIN=https://your-vercel-app.vercel.app
HF_API_TOKEN=optional-huggingface-token
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=llama-3.1-8b-instant
TRANSLATION_PROVIDER=groq
USE_HF_AI=false
```

## Supabase/PostgreSQL Optional Setup

For production PostgreSQL, replace `DATABASE_URL` with a PostgreSQL connection string:

```env
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE
```

The project includes `psycopg[binary]` in `requirements.txt`
