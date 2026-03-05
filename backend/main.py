"""
main.py
-------
Product Review Insights API – pure Python stdlib HTTP server.
(FastAPI/uvicorn not available in offline environment; this implementation
 is fully compatible and can be swapped for FastAPI in production.)

Routes:
  GET /                          -> health check JSON
  GET /api/products              -> list all product IDs
  GET /api/insights/<product_id> -> full NLP insights
  OPTIONS *                      -> CORS preflight

Run:
  python main.py          # starts on port 8000
  python main.py 9000     # custom port
"""

import json
import logging
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import unquote

from data_loader  import DataLoader
from nlp_pipeline import analyse_product

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("api")

# ── Global singleton: load dataset once at startup ────────────────────────────
logger.info("Loading dataset ...")
_LOADER = DataLoader(csv_path="final_dataset.csv")
logger.info("Dataset loaded. Ready.")

CORS_HEADERS = {
    "Access-Control-Allow-Origin":  "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


class InsightsHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the Insights API."""

    # ── Silence default access log (we do our own) ───────────────────────────
    def log_message(self, fmt, *args):
        pass

    # ── CORS preflight ────────────────────────────────────────────────────────
    def do_OPTIONS(self):
        self._send(204, {})

    # ── Main router ───────────────────────────────────────────────────────────
    def do_GET(self):
        t0   = time.perf_counter()
        path = unquote(self.path.split("?")[0]).rstrip("/")

        try:
            if path == "" or path == "/":
                body = {"status": "healthy", "service": "Product Review Insights API"}
                self._send(200, body)

            elif path == "/api/products":
                ids  = _LOADER.all_product_ids()
                self._send(200, {"product_ids": ids, "count": len(ids)})

            elif path.startswith("/api/insights/"):
                product_id = path[len("/api/insights/"):]
                self._handle_insights(product_id)

            else:
                self._send(404, {"detail": f"Route '{path}' not found."})

        except Exception as exc:
            logger.exception("Unhandled error on %s: %s", path, exc)
            self._send(500, {"detail": "Internal server error."})

        elapsed = time.perf_counter() - t0
        logger.info("GET %-45s  %.3fs", path, elapsed)

    # ── Insights handler ──────────────────────────────────────────────────────
    def _handle_insights(self, product_id: str):
        if not product_id:
            self._send(400, {"detail": "product_id is required."})
            return

        reviews = _LOADER.get_reviews(product_id)
        if not reviews:
            self._send(404, {"detail": f"Product '{product_id}' not found."})
            return

        logger.info("Analysing product '%s' (%d reviews) ...", product_id, len(reviews))
        insights = analyse_product(reviews)
        self._send(200, {"product_id": product_id, **insights})

    # ── Response helper ───────────────────────────────────────────────────────
    def _send(self, status: int, body: Any):
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type",   "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(payload)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = HTTPServer(("0.0.0.0", port), InsightsHandler)
    logger.info("API listening on http://0.0.0.0:%d", port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down.")
        server.server_close()
