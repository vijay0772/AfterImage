
# AfterImage - Chat with PDF

PDF Q&A application with evidence highlighting. Upload a PDF, ask questions, and see answers with highlighted evidence in the document.

## Running the application

### 1. Backend (required)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # or `.venv\Scripts\activate` on Windows
pip install -r requirements.txt
# Copy .env.example to .env and add your OPENAI_API_KEY
python -m uvicorn app.main:app --reload --port 8000
```

### 2. Frontend
```bash
cd Frontend
npm install
# Ensure .env has VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

Open http://localhost:3000. Upload a PDF and ask questions.
  