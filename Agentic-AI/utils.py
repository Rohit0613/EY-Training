# utils.py (ensure these exist)
import re
def parse_price(text):
    if not text: return None
    m = re.search(r"₹\s*([0-9]+(?:\.[0-9]+)?)", text)
    if m: return float(m.group(1))
    m2 = re.search(r"(\d+)\s*(?:Rs|INR)", text)
    if m2: return float(m2.group(1))
    return None

def parse_eta(text):
    if not text: return None
    m = re.search(r"(\d+)\s*(?:day|days|d)\b", text)
    if m: return int(m.group(1))
    if re.search(r"\btomorrow\b", text, re.I): return 1
    if re.search(r"\btoday\b", text, re.I): return 0
    return None

def score_supplier(row):
    # row must have parsed_price and parsed_eta
    price = row.get("parsed_price") or 1e9
    eta = row.get("parsed_eta") if row.get("parsed_eta") is not None else 7
    # lower is better — weight price more
    return price * 0.7 + eta * 0.3 * 10

def recommend_supplier(rows):
    best = None
    best_score = 1e18
    for r in rows:
        sc = score_supplier(r)
        if sc < best_score:
            best_score = sc
            best = r
    return best
