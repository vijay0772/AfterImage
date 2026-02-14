# AfterImage

PDF Q&A app — upload a PDF, ask questions, and get answers with highlighted evidence.

## Features

- **Upload PDFs** and extract line-based text
- **Ask questions** in natural language
- **View answers** with evidence quotes and PDF highlights
- **Download** PDFs with highlights burned in
- **Flowsheet support** for clinical vitals (blood pressure, pulse, SpO2, etc.) by time

## Project Structure

```
AfterImage/
├── Frontend/     # React + Vite app
├── Backend/      # FastAPI Python API
├── render.yaml   # Render backend config
└── README.md
```

## Local Development

### Backend

```bash
cd Backend
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Create `Backend/.env`:

```
OPENAI_API_KEY=your_key
PDF_DIR=app/data/pdfs
ARTIFACTS_DIR=app/data/artifacts
OPENAI_MODEL=gpt-4o-mini
```

Run:

```bash
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd Frontend
npm install
```

Create `Frontend/.env`:

```
VITE_API_BASE_URL=http://localhost:8000
```

Run:

```bash
npm run dev
```

Open http://localhost:5173

## Deployment

- **Frontend** → Vercel (builds from `Frontend/`)
- **Backend** → Render (uses `Backend/Dockerfile`, `render.yaml`)

Push to your connected branch to trigger automatic deploys.

## Environment Variables

| Variable       | Description                    |
|----------------|--------------------------------|
| `OPENAI_API_KEY` | OpenAI API key (backend)     |
| `VITE_API_BASE_URL` | Backend API URL (frontend) |
