from datetime import datetime, timezone

import pandas as pd
from cryptofeed.feed import Feed as BaseFeed


class Feed(BaseFeed):
    def std_symbol_to_exchange_symbol(self, symbol: str) -> str:
        """Standard symbol to exchange symbol.

        There are certainly valid reasons to standardize symbols,
        but there are also reasons to not care
        """
        return symbol

    def exchange_symbol_to_std_symbol(self, symbol: str) -> str:
        """Exchange symbol to standard symbol.

        Ditto
        """
        return symbol

    def parse_datetime(self, value: str, unit: str = "ns") -> datetime:
        """Parse datetime with pandas for nanosecond accuracy."""
        return pd.to_datetime(value, unit=unit).replace(tzinfo=timezone.utc)
