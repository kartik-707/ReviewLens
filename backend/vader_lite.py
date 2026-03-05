"""
vader_lite.py
-------------
Self-contained VADER sentiment scorer with expanded lexicon.
"""

import re
import math

VADER_LEXICON = {
    # Very positive
    "outstanding": 3.7, "excellent": 3.7, "amazing": 3.7, "fantastic": 3.7,
    "wonderful": 3.7, "superb": 3.6, "exceptional": 3.5, "brilliant": 3.5,
    "perfect": 3.4, "incredible": 3.4, "awesome": 3.3, "magnificent": 3.3,
    "splendid": 3.2, "terrific": 3.2, "great": 3.1, "love": 3.0,
    "loved": 3.0, "loves": 3.0, "best": 3.0, "superfast": 2.9,
    "recommend": 2.9, "recommended": 2.9, "impressive": 2.8,
    "delighted": 2.8, "thrilled": 2.7, "pleased": 2.7, "phenomenal": 3.5,
    "flawless": 3.2, "exceptional": 3.5, "remarkable": 3.1, "stellar": 3.2,
    "top-notch": 3.0, "first-rate": 2.9, "top": 2.1, "superior": 2.8,
    # Moderately positive
    "good": 1.9, "nice": 1.9, "happy": 1.9, "enjoy": 1.8, "enjoyed": 1.8,
    "like": 1.8, "liked": 1.8, "likes": 1.8, "useful": 1.7, "helpful": 1.7,
    "easy": 1.6, "convenient": 1.6, "reliable": 1.6, "solid": 1.5,
    "fast": 1.5, "quick": 1.5, "smooth": 1.5, "clean": 1.4,
    "comfortable": 1.4, "decent": 1.3, "satisfying": 1.3, "satisfied": 1.3,
    "satisfactory": 1.2, "adequate": 1.0, "reasonable": 1.0, "ok": 0.9,
    "okay": 0.9, "fine": 0.8, "acceptable": 0.8, "works": 0.5,
    "sturdy": 1.6, "durable": 1.7, "lightweight": 1.3, "portable": 1.2,
    "bright": 1.4, "sharp": 1.4, "crisp": 1.4, "clear": 1.3,
    "responsive": 1.5, "accurate": 1.5, "precise": 1.4, "strong": 1.3,
    "improved": 1.4, "improvement": 1.3, "upgrade": 1.2, "worth": 1.4,
    "value": 1.1, "bargain": 1.8, "affordable": 1.5, "inexpensive": 1.2,
    "spacious": 1.3, "roomy": 1.2, "generous": 1.3, "bonus": 1.5,
    "innovative": 1.8, "elegant": 1.7, "sleek": 1.6, "stylish": 1.5,
    "intuitive": 1.7, "seamless": 1.8, "effortless": 1.7,
    # Very negative
    "terrible": -3.7, "horrible": -3.7, "dreadful": -3.6, "awful": -3.5,
    "atrocious": -3.5, "abysmal": -3.4, "disgusting": -3.4, "hate": -3.2,
    "hated": -3.2, "worst": -3.2, "worthless": -3.1, "useless": -3.0,
    "disaster": -3.0, "garbage": -2.9, "trash": -2.9, "junk": -2.8,
    "scam": -2.8, "fraud": -2.8, "broken": -2.7, "defective": -2.7,
    "rubbish": -2.7, "pathetic": -2.6, "appalling": -3.2, "horrendous": -3.5,
    "dreadful": -3.2, "deplorable": -3.1, "unacceptable": -2.8,
    "outrageous": -2.9, "infuriating": -2.8, "unbearable": -2.9,
    "nightmarish": -3.0, "disastrous": -3.1, "catastrophic": -3.2,
    # Moderately negative
    "bad": -1.9, "poor": -1.9, "disappointing": -1.9,
    "disappointed": -1.8, "disappoints": -1.8, "frustrating": -1.8,
    "frustrated": -1.7, "annoying": -1.7, "annoyed": -1.7,
    "slow": -1.5, "difficult": -1.5, "hard": -1.2, "issue": -1.0,
    "problem": -1.1, "problems": -1.1, "issues": -1.0, "bug": -1.0,
    "bugs": -1.0, "crash": -1.3, "crashes": -1.3, "fail": -1.5,
    "fails": -1.5, "failed": -1.5, "failure": -1.5,
    "cheap": -0.7, "flimsy": -1.5, "uncomfortable": -1.4,
    "unreliable": -1.5, "inaccurate": -1.4, "wrong": -1.3,
    "weak": -1.1, "limited": -0.8, "lack": -1.0, "missing": -0.9,
    "stopped": -1.2, "stop": -0.7, "overpriced": -2.0, "expensive": -0.9,
    "waste": -2.1, "wasted": -2.0, "money": -0.3, "useless": -3.0,
    "pointless": -2.0, "unnecessary": -1.2, "ridiculous": -2.0,
    "absurd": -1.8, "insane": -1.5, "unbelievable": -1.3,
    "empty": -1.5, "nothing": -1.0, "broke": -2.0, "breaking": -1.8,
    "cracked": -1.9, "damaged": -1.8, "scratched": -1.3, "dented": -1.3,
    "melted": -2.0, "burned": -2.0, "burnt": -2.0, "exploded": -3.0,
    "overheating": -2.2, "overheat": -2.2, "hot": -0.8, "heating": -1.0,
    "lagging": -1.5, "lag": -1.3, "freezing": -1.5, "froze": -1.5,
    "freeze": -1.4, "glitchy": -1.6, "glitch": -1.4, "glitches": -1.5,
    "error": -1.3, "errors": -1.3, "fault": -1.5, "faulty": -1.8,
    "defect": -1.8, "defective": -1.9, "malfunction": -2.0,
    "malfunctioning": -2.0, "unusable": -2.5, "unresponsive": -2.0,
    "dead": -2.0, "died": -2.0, "dying": -1.8,
    "return": -0.8, "returned": -0.9, "refund": -1.0, "returning": -0.9,
    "avoid": -1.8, "beware": -2.0, "warning": -1.5, "caution": -1.2,
    "regret": -2.0, "regretted": -2.1, "mistake": -1.8, "misleading": -2.0,
    "lied": -2.2, "lying": -2.0, "deceptive": -2.3, "fake": -2.2,
    "counterfeit": -2.5, "knockoff": -2.0, "inferior": -2.0,
    "substandard": -2.0, "subpar": -1.9, "mediocre": -1.5,
    "underwhelming": -1.7, "overrated": -1.8, "overhyped": -1.6,
    "inconsistent": -1.4, "unstable": -1.6, "unreliable": -1.8,
    "complicated": -1.3, "confusing": -1.3, "clunky": -1.5, "bulky": -1.0,
    "heavy": -0.8, "thick": -0.5, "outdated": -1.3, "obsolete": -1.5,
    "short": -0.8, "shorter": -0.9, "shortest": -1.0,
    "dim": -1.2, "blurry": -1.5, "pixelated": -1.4, "grainy": -1.2,
    "noisy": -1.3, "loud": -0.7, "quiet": 0.3, "silent": 0.5,
    "sticky": -1.0, "slippery": -1.0, "wobbly": -1.3, "loose": -1.2,
    "tight": -0.6, "stiff": -0.8, "scratchy": -1.2,
    "point": -0.5, "cable": -0.2, "adapter": -0.1,
}

_NEGATORS = {"not", "never", "no", "cannot", "cant", "don't", "doesn't",
             "didn't", "won't", "wouldn't", "couldn't", "shouldn't",
             "isn't", "aren't", "wasn't", "weren't", "hardly", "barely",
             "dont", "doesnt", "didnt", "wont", "wouldnt", "couldnt",
             "shouldnt", "isnt", "arent", "wasnt", "werent"}

_BOOSTERS = {"very": 0.293, "extremely": 0.293, "incredibly": 0.293,
             "absolutely": 0.293, "totally": 0.293, "really": 0.293,
             "quite": 0.193, "rather": 0.193, "somewhat": -0.1,
             "super": 0.293, "highly": 0.2, "completely": 0.2,
             "utterly": 0.293, "truly": 0.2, "deeply": 0.2,
             "barely": -0.2, "slightly": -0.1, "kind": -0.1,
             "sort": -0.1, "little": -0.1}

# Negative phrase patterns (multi-word expressions)
_NEG_PHRASES = [
    ("waste of money", -2.5), ("waste of time", -2.3),
    ("out of your mind", -2.0), ("out of mind", -1.8),
    ("no product", -2.2), ("not worth", -2.0), ("not work", -2.0),
    ("not working", -2.2), ("does not work", -2.5), ("didn't work", -2.5),
    ("doesnt work", -2.5), ("stopped working", -2.3), ("no point", -1.8),
    ("whats the point", -1.8), ("what's the point", -1.8),
    ("don't buy", -2.5), ("dont buy", -2.5), ("do not buy", -2.5),
    ("not worth it", -2.2), ("not recommend", -2.3), ("not recommended", -2.3),
    ("would not recommend", -2.5), ("wouldn't recommend", -2.5),
    ("complete waste", -2.8), ("total waste", -2.8), ("utter waste", -2.8),
    ("money back", -1.8), ("sent back", -1.5), ("sent it back", -1.8),
    ("falling apart", -2.0), ("fell apart", -2.2), ("broke after", -2.3),
    ("stopped after", -2.0), ("died after", -2.2), ("dead on arrival", -3.0),
    ("out of box", -1.5), ("right out of the box", -0.5),
    ("never again", -2.3), ("save your money", -2.2),
    ("piece of junk", -3.0), ("piece of trash", -3.0), ("piece of garbage", -3.0),
    ("rip off", -2.5), ("ripped off", -2.5), ("highway robbery", -2.8),
]

# Positive phrase patterns
_POS_PHRASES = [
    ("worth every penny", 3.0), ("worth the money", 2.5), ("great value", 2.5),
    ("highly recommend", 2.8), ("love it", 2.8), ("love this", 2.7),
    ("works great", 2.5), ("works perfectly", 2.8), ("works well", 2.2),
    ("exceeded expectations", 3.0), ("exceeded my expectations", 3.0),
    ("very happy", 2.5), ("very pleased", 2.5), ("very satisfied", 2.4),
    ("best purchase", 2.8), ("great purchase", 2.5), ("good purchase", 2.0),
    ("exactly what i expected", 1.5), ("exactly as described", 1.8),
    ("as expected", 1.2), ("as advertised", 1.5),
    ("fast delivery", 2.0), ("quick delivery", 2.0), ("fast shipping", 2.0),
    ("easy to use", 2.2), ("easy to set up", 2.0), ("easy setup", 2.0),
    ("battery life", 0.3), ("long battery", 2.0), ("great battery", 2.5),
]


def _tokenise(text: str):
    return re.findall(r"\b\w+(?:'\w+)?\b", text.lower())


def polarity_scores(text: str) -> dict:
    text_lower = text.lower()
    tokens = _tokenise(text)
    scores = []

    # Check multi-word phrases first
    for phrase, val in _NEG_PHRASES + _POS_PHRASES:
        if phrase in text_lower:
            scores.append(val)

    # Token-level scoring
    n = len(tokens)
    for i, token in enumerate(tokens):
        val = VADER_LEXICON.get(token)
        if val is None:
            continue

        # Booster
        if i > 0:
            booster = _BOOSTERS.get(tokens[i - 1], 0)
            if val >= 0:
                val += booster
            else:
                val -= booster

        # Negation window of 3
        negated = any(tokens[max(0, i - k)] in _NEGATORS for k in range(1, 4))
        if negated:
            val *= -0.74

        scores.append(val)

    if not scores:
        return {"neg": 0.0, "neu": 1.0, "pos": 0.0, "compound": 0.0}

    # Punctuation emphasis
    punct_boost = min(text.count("!") * 0.292, 4 * 0.292)
    allcaps_boost = 0.733 if (text.isupper() and any(c.isalpha() for c in text)) else 0.0

    raw_sum = sum(scores)
    if raw_sum > 0:
        raw_sum += punct_boost + allcaps_boost
    elif raw_sum < 0:
        raw_sum -= punct_boost + allcaps_boost

    compound = raw_sum / math.sqrt(raw_sum ** 2 + 15)
    compound = max(-1.0, min(1.0, round(compound, 4)))

    pos_sum = sum(s for s in scores if s > 0)
    neg_sum = sum(abs(s) for s in scores if s < 0)
    total   = pos_sum + neg_sum + len(scores) * 0.001

    pos = round(pos_sum / total, 3)
    neg = round(neg_sum / total, 3)
    neu = round(max(0.0, 1.0 - pos - neg), 3)

    return {"neg": neg, "neu": neu, "pos": pos, "compound": compound}