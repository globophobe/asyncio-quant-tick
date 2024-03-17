def normalize_symbol(feed: str, symbol: str) -> str:
    """Normalize symbol."""
    for char in ("-", "/", "_"):
        symbol = symbol.replace(char, "")
    if feed == "upbit":
        symbol = symbol[3:] + symbol[:3]  # Reversed
    return symbol
