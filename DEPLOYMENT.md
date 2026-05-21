# ALDST Deployment Guide

This project is designed for a split deployment:

- Frontend: Vercel
- Backend: Render or Railway
- Database: SQLite for local development, PostgreSQL/Supabase for production

## Backend on Render or Railway

Use the `backend` folder as the service root.

Install command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Environment variables:

```env
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE
SECRET_KEY=use-a-long-random-secret
FRONTEND_ORIGIN=https://your-vercel-app.vercel.app
HF_API_TOKEN=optional-huggingface-token
USE_HF_AI=false
```

If you deploy without `HF_API_TOKEN`, the app still works with local structured note and flashcard generation. Live translation will show a configuration message.

## Frontend on Vercel

Use the `frontend` folder as the Vercel project root.

Build command:

```bash
npm run build
```

Output directory:

```text
dist
```

Environment variable:

```env
VITE_API_URL=https://your-backend-url/api
```

## Local Ports

If Windows blocks port `8000`, run the backend on `8010`:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

Then set this in `frontend/.env`:

```env
VITE_API_URL=http://127.0.0.1:8010/api
```
