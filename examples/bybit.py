#!/usr/bin/env python3
from cryptofeed import FeedHandler
from cryptofeed.defines import TRADES

from quant_tick.exchanges import Bybit
from quant_tick.trades import (
    CandleCallback,
    SignificantTradeCallback,
    TradeCallback,
)


async def candles(candle: dict, timestamp: float) -> None:
    """Candles."""
    print(candle)


if __name__ == "__main__":
    fh = FeedHandler()
    fh.add_feed(
        Bybit(
            symbols=["BTCUSD"],
            channels=[TRADES],
            callbacks={
                TRADES: TradeCallback(
                    SignificantTradeCallback(
                        CandleCallback(candles, window_seconds=60),
                        window_seconds=60,
                        significant_trade_filter=1_000,
                    ),
                )
            },
        )
    )
    fh.run()
