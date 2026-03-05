"""
nlp_pipeline.py
---------------
Core NLP pipeline - zero external ML dependencies (stdlib + vader_lite.py).

Pipeline stages:
  1. Text preprocessing  - sentence splitting, cleaning
  2. Aspect extraction   - keyword/n-gram based with seed vocabulary
  3. Aspect-level VADER sentiment scoring
  4. Evidence extraction - best supporting quote per aspect x polarity
  5. Aggregation         - ranked aspects, pros & cons
  6. Summary + confidence
"""

import logging
import math
import re
import statistics
from collections import defaultdict
from typing import Dict, List, Tuple

from vader_lite import polarity_scores

logger = logging.getLogger(__name__)

MIN_REVIEWS   = 5
_MIN_MENTIONS = 2
MAX_EVIDENCE  = 3

SEED_ASPECTS: Dict[str, List[str]] = {
    "Battery":          ["battery", "charge", "charging", "power", "mah", "drain"],
    "Screen":           ["screen", "display", "resolution", "brightness", "pixel", "lcd", "oled"],
    "Performance":      ["performance", "speed", "processor", "lag", "fast", "slow", "cpu", "ram", "responsive", "freezes"],
    "Camera":           ["camera", "photo", "picture", "image", "lens", "megapixel", "selfie", "video", "recording"],
    "Build Quality":    ["build", "quality", "material", "plastic", "metal", "finish", "design", "sturdy", "durable", "fragile"],
    "Customer Service": ["customer", "service", "support", "return", "refund", "warranty", "seller", "delivery", "shipping"],
    "Price":            ["price", "value", "cost", "worth", "expensive", "cheap", "affordable", "overpriced", "deal"],
    "Storage":          ["storage", "memory", "capacity", "gb", "space", "expandable", "microsd"],
    "Software":         ["software", "app", "android", "ios", "update", "bug", "ui", "interface", "os", "bloatware"],
    "Sound":            ["sound", "audio", "speaker", "volume", "bass", "headphone", "earphone", "microphone"],
    "Size / Weight":    ["size", "weight", "portable", "thin", "light", "heavy", "bulky", "compact"],
    "Ease of Use":      ["easy", "simple", "setup", "intuitive", "complicated", "navigation"],
}

_ASPECT_TOKENS: Dict[str, set] = {asp: set(kws) for asp, kws in SEED_ASPECTS.items()}


def analyse_product(reviews: List[dict]) -> dict:
    if len(reviews) < MIN_REVIEWS:
        return {
            "status":       "insufficient_data",
            "message":      f"Only {len(reviews)} review(s) found. At least {MIN_REVIEWS} are needed.",
            "review_count": len(reviews),
        }

    sentences         = _extract_sentences(reviews)
    aspect_sentences  = _assign_sentences_to_aspects(sentences)
    aspect_sentences  = {asp: sents for asp, sents in aspect_sentences.items() if len(sents) >= _MIN_MENTIONS}

    if not aspect_sentences:
        return _build_overall_only(reviews)

    aspect_sentiments = {asp: _score_aspect(sents) for asp, sents in aspect_sentences.items()}

    ranked_aspects = sorted(aspect_sentiments, key=lambda a: len(aspect_sentences[a]), reverse=True)

    pros, cons = _extract_pros_cons(aspect_sentiments, aspect_sentences)
    overall    = _overall_summary(reviews, aspect_sentiments)

    return {
        "status":       "ok",
        "review_count": len(reviews),
        "overall":      overall,
        "aspects": [
            {
                "name":          asp,
                "sentiment":     aspect_sentiments[asp]["label"],
                "score":         round(aspect_sentiments[asp]["compound"], 3),
                "positive_pct":  round(aspect_sentiments[asp]["pos_pct"], 1),
                "negative_pct":  round(aspect_sentiments[asp]["neg_pct"], 1),
                "mention_count": len(aspect_sentences[asp]),
            }
            for asp in ranked_aspects
        ],
        "pros": pros,
        "cons": cons,
    }


_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

def _extract_sentences(reviews: List[dict]) -> List[dict]:
    sentences = []
    for review in reviews:
        for sent in _SPLIT_RE.split(review["text"]):
            sent = sent.strip()
            if len(sent.split()) < 4:
                continue
            vs = polarity_scores(sent)
            sentences.append({
                "text":     sent,
                "rating":   review["rating"],
                "compound": vs["compound"],
                "pos":      vs["pos"],
                "neg":      vs["neg"],
            })
    return sentences


def _sentence_aspects(text: str) -> List[str]:
    tokens = set(re.findall(r"\b[\w-]+\b", text.lower()))
    return [asp for asp, kws in _ASPECT_TOKENS.items() if kws & tokens]


def _assign_sentences_to_aspects(sentences: List[dict]) -> Dict[str, List[dict]]:
    bucket: Dict[str, List[dict]] = defaultdict(list)
    for sent in sentences:
        for aspect in _sentence_aspects(sent["text"]):
            bucket[aspect].append(sent)
    return dict(bucket)


def _score_aspect(sents: List[dict]) -> dict:
    weighted, total_w = [], 0.0
    for s in sents:
        w = 1.3 if s["rating"] <= 2 else (0.9 if s["rating"] >= 4 else 1.0)
        weighted.append(s["compound"] * w)
        total_w += w

    mean_c    = sum(weighted) / total_w if total_w else 0.0
    n         = len(sents)
    pos_count = sum(1 for s in sents if s["compound"] >= 0.05)
    neg_count = sum(1 for s in sents if s["compound"] <= -0.05)

    if mean_c >= 0.10:
        label = "Positive"
    elif mean_c <= -0.10:
        label = "Negative"
    else:
        label = "Neutral"

    return {
        "compound": mean_c,
        "label":    label,
        "pos_pct":  100.0 * pos_count / n,
        "neg_pct":  100.0 * neg_count / n,
    }


def _trim_quote(text: str, max_chars: int = 220) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "..."


def _extract_pros_cons(
    aspect_sentiments: Dict[str, dict],
    aspect_sentences:  Dict[str, List[dict]],
) -> Tuple[List[dict], List[dict]]:
    pros: List[dict] = []
    cons: List[dict] = []

    for aspect, sentiment in aspect_sentiments.items():
        sents    = aspect_sentences[aspect]
        compound = sentiment["compound"]

        if compound >= 0.10:
            evidence_sents = sorted(
                (s for s in sents if s["compound"] >= 0.05),
                key=lambda s: s["compound"], reverse=True,
            )[:MAX_EVIDENCE]
            if evidence_sents:
                pros.append({
                    "aspect":   aspect,
                    "score":    round(compound, 3),
                    "evidence": [_trim_quote(s["text"]) for s in evidence_sents],
                })

        elif compound <= -0.10:
            evidence_sents = sorted(
                (s for s in sents if s["compound"] <= -0.05),
                key=lambda s: s["compound"],
            )[:MAX_EVIDENCE]
            if evidence_sents:
                cons.append({
                    "aspect":   aspect,
                    "score":    round(compound, 3),
                    "evidence": [_trim_quote(s["text"]) for s in evidence_sents],
                })

    pros.sort(key=lambda x: x["score"], reverse=True)
    cons.sort(key=lambda x: x["score"])
    return pros, cons


def _overall_summary(reviews: List[dict], aspect_sentiments: Dict[str, dict]) -> dict:
    n          = len(reviews)
    avg_rating = statistics.mean(r["rating"] for r in reviews)
    compounds  = [a["compound"] for a in aspect_sentiments.values()]
    overall_c  = statistics.mean(compounds) if compounds else 0.0

    volume_score    = min(50.0, 50.0 * math.log1p(n) / math.log1p(500))
    agreement_score = max(0.0, 30.0 * (1.0 - min(statistics.stdev(compounds) / 0.5, 1.0))) if len(compounds) > 1 else 15.0
    coverage_score  = min(20.0, 20.0 * len(aspect_sentiments) / 6.0)
    confidence      = round(volume_score + agreement_score + coverage_score, 1)

    top_pro = max(
        (a for a, s in aspect_sentiments.items() if s["compound"] >= 0.10),
        key=lambda a: aspect_sentiments[a]["compound"], default=None,
    )
    top_con = min(
        (a for a, s in aspect_sentiments.items() if s["compound"] <= -0.10),
        key=lambda a: aspect_sentiments[a]["compound"], default=None,
    )

    tone  = "mostly positive" if overall_c >= 0.15 else ("mostly negative" if overall_c <= -0.15 else "mixed")
    parts = [f"Based on {n} reviews, overall sentiment is {tone} (avg. rating {avg_rating:.1f} / 5)."]
    if top_pro:
        parts.append(f"Customers especially praise {top_pro}.")
    if top_con:
        parts.append(f"Common complaints focus on {top_con}.")

    return {
        "narrative":        " ".join(parts),
        "average_rating":   round(avg_rating, 2),
        "overall_compound": round(overall_c, 3),
        "confidence":       confidence,
    }


def _build_overall_only(reviews: List[dict]) -> dict:
    avg_rating = statistics.mean(r["rating"] for r in reviews)
    return {
        "status":       "ok",
        "review_count": len(reviews),
        "overall": {
            "narrative":        f"Based on {len(reviews)} reviews (avg. rating {avg_rating:.1f} / 5). No specific aspects were identified.",
            "average_rating":   round(avg_rating, 2),
            "overall_compound": 0.0,
            "confidence":       20.0,
        },
        "aspects": [],
        "pros":    [],
        "cons":    [],
    }
