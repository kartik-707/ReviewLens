"""
data_loader.py
--------------
Responsible for loading the CSV dataset once at startup and providing
fast lookup by product_id.  All heavy I/O happens here so the rest of
the pipeline receives clean Python objects.
"""

import logging
import re
from pathlib import Path
from typing import Dict, List

import pandas as pd

logger = logging.getLogger(__name__)

# ── Column aliases ──────────────────────────────────────────────────────────
# The BOM character (\ufeff) sometimes prefixes the first column name.
_ID_ALIASES      = {"productid", "product_id", "id", "\ufeffid"}
_TEXT_ALIASES    = {"text", "reviews.text", "review_text", "reviewtext"}
_RATING_ALIASES  = {"score", "reviews.rating", "rating"}
_DATE_ALIASES    = {"time", "reviews.dateadded", "review_date", "date"}


def _find_col(columns: List[str], aliases: set) -> str:
    """Return the first column name (case-insensitive) that matches an alias."""
    for col in columns:
        if col.strip().lower().replace(" ", "") in aliases:
            return col
    raise KeyError(f"Could not find a column matching any of {aliases}. "
                   f"Available columns: {columns}")


class DataLoader:
    """Loads the CSV once and builds a {product_id -> list[review_dict]} index."""

    def __init__(self, csv_path: str = "final_dataset.csv"):
        self.csv_path = Path(csv_path)
        # Map: product_id (str) → list of review dicts
        self._index: Dict[str, List[dict]] = {}
        self._load()

    # ── Public API ──────────────────────────────────────────────────────────

    def get_reviews(self, product_id: str) -> List[dict]:
        """Return all reviews for *product_id*, or an empty list if unknown."""
        return self._index.get(product_id, [])

    def all_product_ids(self) -> List[str]:
        return list(self._index.keys())

    # ── Private helpers ─────────────────────────────────────────────────────

    def _load(self) -> None:
        logger.info("Loading dataset from %s …", self.csv_path)

        # Read CSV; handle BOM transparently
        df = pd.read_csv(self.csv_path, encoding="utf-8-sig", low_memory=False)
        df.columns = df.columns.str.strip()          # strip accidental whitespace

        cols = list(df.columns)
        id_col     = _find_col(cols, _ID_ALIASES)
        text_col   = _find_col(cols, _TEXT_ALIASES)
        rating_col = _find_col(cols, _RATING_ALIASES)

        # Date column is optional
        try:
            date_col = _find_col(cols, _DATE_ALIASES)
        except KeyError:
            date_col = None
            logger.warning("No date column found; review_date will be null.")

        # Drop rows with no text or no product id
        df = df.dropna(subset=[id_col, text_col])
        df[id_col] = df[id_col].astype(str).str.strip()

        # Convert rating to float; fill missing with neutral 3.0
        df[rating_col] = pd.to_numeric(df[rating_col], errors="coerce").fillna(3.0)

        # Build index
        for _, row in df.iterrows():
            pid = row[id_col]
            if not pid:
                continue
            review = {
                "text":   self._clean_text(str(row[text_col])),
                "rating": float(row[rating_col]),
                "date":   str(row[date_col]) if date_col else None,
            }
            self._index.setdefault(pid, []).append(review)

        logger.info(
            "Dataset loaded: %d products, %d total reviews.",
            len(self._index),
            sum(len(v) for v in self._index.values()),
        )

    @staticmethod
    def _clean_text(text: str) -> str:
        """Light cleaning: collapse whitespace, drop non-printable chars."""
        text = re.sub(r"[^\x20-\x7E\n]", " ", text)   # keep printable ASCII
        text = re.sub(r"\s+", " ", text).strip()
        return text
