import re

def parse_price(price_str: str) -> float | None:
    """
    Parses a price string (e.g., '$1.23 (5 bids)') and returns the float value.
    """
    if not price_str:
        return None
    
    # Use regex to find the first number (integer or float) in the string
    match = re.search(r'(\d+\.?\d*)', price_str)
    if match:
        try:
            return float(match.group(1))
        except (ValueError, IndexError):
            return None
    return None 