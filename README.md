# Product Review Insights

Aspect-level sentiment analysis on Amazon product reviews.

## Quick Start

### Backend (Python — no extra installs needed)
```bash
cd backend
python3 main.py          # starts on http://localhost:8000
```

### Frontend (standalone)
Open `frontend/index.html` directly in a browser.
It connects to `http://localhost:8000` automatically.

### Frontend (Vite dev server — requires npm)
```bash
cd frontend
npm install
npm run dev              # http://localhost:5173
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check |
| GET | `/api/products` | List all product IDs |
| GET | `/api/insights/{product_id}` | Full NLP insights |

## Sample Product IDs
- `AVphgVaX1cnluZ0-DR74`  (9 393 reviews)
- `AVpfl8cLLJeJML43AE3S`  (5 613 reviews)
- `AV1YE_muvKc47QAVgpwE`  (4 350 reviews)
- `AVqkIhwDv8e3D1O-lebb`  (2 397 reviews)

## Dependencies
- **Backend**: Python 3.8+ stdlib + `pandas` only
- **Frontend**: CDN-loaded React 18, Recharts, Babel (no build step for dev)
