"""
test_pipeline.py
----------------
Unit tests for the NLP pipeline. Run from the backend/ directory:
    python3 -m pytest test_pipeline.py -v
    # or without pytest:
    python3 test_pipeline.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from vader_lite   import polarity_scores
from nlp_pipeline import (
    _extract_sentences,
    _assign_sentences_to_aspects,
    _score_aspect,
    _trim_quote,
    analyse_product,
    MIN_REVIEWS,
)


# ── vader_lite tests ─────────────────────────────────────────────────────────

def test_vader_positive():
    s = polarity_scores("This product is absolutely amazing and fantastic!")
    assert s["compound"] > 0.5, f"Expected strong positive, got {s['compound']}"

def test_vader_negative():
    s = polarity_scores("This is terrible, broken, and completely useless.")
    assert s["compound"] < -0.4, f"Expected strong negative, got {s['compound']}"

def test_vader_neutral():
    s = polarity_scores("The product arrived in a brown cardboard box.")
    assert -0.2 < s["compound"] < 0.2, f"Expected neutral, got {s['compound']}"

def test_vader_negation():
    pos = polarity_scores("This is great.")["compound"]
    neg = polarity_scores("This is not great.")["compound"]
    assert neg < pos, "Negation should reduce positive score"

def test_vader_keys():
    s = polarity_scores("ok")
    assert set(s.keys()) == {"neg", "neu", "pos", "compound"}


# ── Sentence extraction tests ────────────────────────────────────────────────

def test_extract_sentences_basic():
    reviews = [{"text": "Battery life is great. Screen quality is bright and vivid. Performance is fast and responsive.", "rating": 5.0, "date": None}]
    sents = _extract_sentences(reviews)
    assert len(sents) >= 2, f"Expected >=2 sentences, got {len(sents)}: {sents}"
    for s in sents:
        assert "text" in s and "compound" in s and "rating" in s

def test_extract_sentences_filters_short():
    reviews = [{"text": "Good. Bad. The camera takes excellent photos in low light conditions.", "rating": 3.0, "date": None}]
    sents = _extract_sentences(reviews)
    # Short 1-word sentences should be filtered out
    assert all(len(s["text"].split()) >= 4 for s in sents)


# ── Aspect assignment tests ──────────────────────────────────────────────────

def test_aspect_assignment_battery():
    sents = [{"text": "Battery life lasts for days.", "rating": 5.0, "compound": 0.5, "pos": 0.4, "neg": 0.0}]
    result = _assign_sentences_to_aspects(sents)
    assert "Battery" in result

def test_aspect_assignment_multiple():
    sents = [{"text": "Screen brightness and camera quality are both excellent.", "rating": 5.0, "compound": 0.6, "pos": 0.5, "neg": 0.0}]
    result = _assign_sentences_to_aspects(sents)
    assert "Screen" in result or "Camera" in result

def test_aspect_no_match():
    sents = [{"text": "I ordered it last Tuesday and it came.", "rating": 3.0, "compound": 0.0, "pos": 0.0, "neg": 0.0}]
    # May match "Customer Service" due to order/delivery keywords — just ensure no crash
    result = _assign_sentences_to_aspects(sents)
    assert isinstance(result, dict)


# ── Sentiment scoring tests ──────────────────────────────────────────────────

def test_score_aspect_positive():
    sents = [
        {"text": "Battery is amazing", "rating": 5.0, "compound": 0.8, "pos": 0.7, "neg": 0.0},
        {"text": "Battery lasts long",  "rating": 5.0, "compound": 0.6, "pos": 0.5, "neg": 0.0},
    ]
    result = _score_aspect(sents)
    assert result["label"] == "Positive"
    assert result["compound"] > 0

def test_score_aspect_negative():
    sents = [
        {"text": "Battery drains fast",  "rating": 1.0, "compound": -0.6, "pos": 0.0, "neg": 0.5},
        {"text": "Battery is terrible",  "rating": 1.0, "compound": -0.8, "pos": 0.0, "neg": 0.7},
    ]
    result = _score_aspect(sents)
    assert result["label"] == "Negative"
    assert result["compound"] < 0


# ── Trim quote tests ──────────────────────────────────────────────────────────

def test_trim_quote_short():
    q = "Short quote."
    assert _trim_quote(q) == q

def test_trim_quote_long():
    q = "word " * 60  # 300 chars
    trimmed = _trim_quote(q)
    assert len(trimmed) <= 223  # 220 + '...'
    assert trimmed.endswith("...")


# ── Full pipeline tests ──────────────────────────────────────────────────────

def test_pipeline_insufficient_data():
    reviews = [{"text": "Great product.", "rating": 5.0, "date": None}]
    result = analyse_product(reviews)
    assert result["status"] == "insufficient_data"
    assert result["review_count"] == 1

def test_pipeline_full():
    reviews = [
        {"text": f"Battery life is {'excellent' if i % 3 else 'poor'}. Screen is bright and clear. Performance is fast.",
         "rating": 4.0 if i % 3 else 2.0, "date": None}
        for i in range(20)
    ]
    result = analyse_product(reviews)
    assert result["status"] == "ok"
    assert result["review_count"] == 20
    assert "aspects" in result
    assert "pros"    in result
    assert "cons"    in result
    assert "overall" in result
    assert 0 <= result["overall"]["confidence"] <= 100

def test_pipeline_overall_fields():
    reviews = [
        {"text": "Great battery life and excellent screen quality. Very easy to use.",
         "rating": 5.0, "date": None}
        for _ in range(10)
    ]
    result = analyse_product(reviews)
    overall = result["overall"]
    assert "narrative"        in overall
    assert "average_rating"   in overall
    assert "overall_compound" in overall
    assert "confidence"       in overall


# ── Runner ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for fn in tests:
        try:
            fn()
            print(f"  ✓  {fn.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ✗  {fn.__name__}  →  {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed out of {passed + failed} tests.")
    sys.exit(1 if failed else 0)
