import re
from difflib import get_close_matches

def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text

def match_text(user_input: str, valid_texts, cutoff: float = 0.80):
    """
    Returns (True, canonical_text) if the input matches exactly
    or is close enough to one of the valid_texts.
    Otherwise returns (False, None).
    """
    normalized_input = normalize_text(user_input)
    normalized_valid = [normalize_text(v) for v in valid_texts]

    # exact match
    if normalized_input in normalized_valid:
        idx = normalized_valid.index(normalized_input)
        return True, valid_texts[idx]

    # accept if the full valid answer appears inside a longer sentence
    for i, valid in enumerate(normalized_valid):
        if len(valid) >= 6 and valid in normalized_input:
            return True, valid_texts[i]

    # fuzzy match
    close = get_close_matches(normalized_input, normalized_valid, n=1, cutoff=cutoff)
    if close:
        idx = normalized_valid.index(close[0])
        return True, valid_texts[idx]

    return False, None