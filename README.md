# ReviewLens — Product Review Insights Dashboard

ReviewLens is a local web application that performs aspect-level sentiment analysis on Amazon product reviews. Enter a product ID and the system processes every associated review through an NLP pipeline, returning a structured report with sentiment scores, pros and cons, and verbatim evidence quotes pulled directly from the data.

Everything runs locally. No cloud services, no API keys, no internet connection required at runtime.

---

## What It Does

Given a product ID, the dashboard produces:

- **Overview stats** — average rating, total review count, confidence score
- **Aspect sentiment chart** — bar chart showing sentiment scores for aspects like Battery, Screen, Performance, Camera, and more
- **Pros and cons** — expandable cards backed by actual quotes from reviews, never generated or paraphrased
- **Overall summary** — a plain-English description of the product's reception

---

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3 stdlib + pandas |
| HTTP Server | Python `http.server` (no frameworks) |
| Frontend | React 18 + Recharts, single HTML file |
| Sentiment | Custom VADER scorer (pure Python, no installs) |
| Aspect Extraction | Keyword-based sentence matching |

---

## Project Structure

```
product-insights/
├── backend/
│   ├── main.py              REST API server with routing, CORS, and logging
│   ├── data_loader.py       CSV ingestion and product index builder
│   ├── nlp_pipeline.py      Five-stage NLP pipeline
│   ├── vader_lite.py        Self-contained VADER sentiment scorer
│   ├── test_pipeline.py     Unit test suite (17 tests)
│   ├── requirements.txt     Dependency list for production setup
│   └── final_dataset.csv    Reviews dataset (not tracked in git)
└── frontend/
    ├── index.html           Standalone dashboard (no build step needed)
    └── src/                 Vite-compatible component source files
        ├── App.jsx
        ├── api.js
        ├── index.css
        ├── components/
        │   ├── AspectChart.jsx
        │   └── EvidenceCard.jsx
        └── hooks/
            └── useInsights.js
```

---

## Dataset Requirements

Place your reviews CSV in `backend/` and name it `final_dataset.csv`. The loader auto-detects column names so the exact names do not need to match exactly — it looks for the following:

| Required Data | Accepted Column Names |
|---|---|
| Product identifier | `ProductId`, `product_id`, `id` |
| Review text | `Text`, `reviews.text`, `review_text` |
| Star rating (1–5) | `Score`, `reviews.rating`, `rating` |
| Date (optional) | `Time`, `reviews.dateAdded`, `date` |

A minimum of 5 reviews per product is required to generate insights. Products with fewer reviews return a graceful insufficient data message.

---

## Setup

```bash
cd product-insights/backend

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate        # Windows
source venv/bin/activate       # Mac / Linux

# Install the only dependency
pip install pandas
```

---

## Running the Application

You need two terminal windows open at the same time.

**Terminal 1 — Start the backend**
```bash
cd product-insights/backend
.\venv\Scripts\activate
python main.py
```

You should see:
```
Dataset loaded: X products, Y total reviews.
API listening on http://0.0.0.0:8000
```

**Terminal 2 — Serve the frontend**
```bash
cd product-insights/frontend
python -m http.server 3000
```

Then open your browser and go to `http://localhost:3000`.

> Terminal 1 must stay running the entire time you use the dashboard.

---

## API Reference

The backend exposes a simple REST API. All responses are JSON with CORS enabled.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check |
| GET | `/api/products` | List all product IDs in the dataset |
| GET | `/api/insights/{product_id}` | Full NLP insights for a product |

**Example response shape:**
```json
{
  "product_id": "B001E4KFG0",
  "status": "ok",
  "review_count": 928,
  "overall": {
    "narrative": "Based on 928 reviews, overall sentiment is mostly positive (avg. rating 4.3 / 5).",
    "average_rating": 4.3,
    "confidence": 78.4
  },
  "aspects": [
    { "name": "Battery", "sentiment": "Positive", "score": 0.42, "mention_count": 134 }
  ],
  "pros": [
    { "aspect": "Battery", "score": 0.42, "evidence": ["Battery life is absolutely incredible..."] }
  ],
  "cons": [
    { "aspect": "Price", "score": -0.31, "evidence": ["Complete waste of money for what you get."] }
  ]
}
```

---

## How the NLP Pipeline Works

1. **Sentence extraction** — Reviews are split into sentences and each is scored with VADER sentiment.
2. **Aspect assignment** — Sentences are matched to 12 product aspects (Battery, Screen, Performance, Camera, Build Quality, Customer Service, Price, Storage, Software, Sound, Size and Weight, Ease of Use) by keyword token overlap.
3. **Sentiment scoring** — Sentences are aggregated per aspect. Low-star reviews are weighted 1.3x to prevent negative signals being diluted by review volume.
4. **Evidence extraction** — Pros surface aspects with a strong positive average. Cons surface aspects where either the average is negative OR more than 20 percent of sentences are negative, ensuring minority complaints are visible even on well-reviewed products.
5. **Confidence scoring** — A 0–100 score is calculated from review volume, sentiment consistency, and aspect coverage.

---

## Running Tests

```bash
cd product-insights/backend
.\venv\Scripts\activate
python test_pipeline.py
```

All 17 tests should pass covering the VADER scorer, sentence extractor, aspect matching, sentiment aggregation, and full pipeline.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Page is blank | Go to `http://localhost:3000`, do not open the HTML file directly |
| Product not found | Run `python -c "import pandas as pd; print(pd.read_csv('final_dataset.csv')['ProductId'].value_counts().head(10))"` to get valid IDs |
| CSV not found on startup | Make sure `final_dataset.csv` is inside `backend/`, not the root folder |
| Port already in use | Run `python main.py 9000` and update `API_BASE` in `index.html` to match |
| Ctrl+C not working | Close the terminal window and open a new one |
| venv activation blocked on Windows | Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
