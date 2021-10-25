from decimal import Decimal


def decimal_to_str(data: dict):
    for key, value in data.items():
        if isinstance(value, dict):
            data[key] = decimal_to_str(value)
        elif isinstance(value, list):
            for index, v in enumerate(value):
                if isinstance(v, dict):
                    data[key][index] = decimal_to_str(v)
                elif isinstance(v, Decimal):
                    data[key][index] = str(v)
        elif isinstance(value, Decimal):
            data[key] = str(value)
    return data


def normalize_symbol(feed: str, symbol: str):
    for char in ("-", "/", "_"):
        symbol = symbol.replace(char, "")
    if feed == "upbit":
        symbol = symbol[3:] + symbol[:3]  # Reversed
    return symbol
