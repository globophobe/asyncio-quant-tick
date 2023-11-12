#!/usr/bin/env python3
from cryptofeed import FeedHandler
from cryptofeed.defines import TRADES

from cryptofeed_experiments.exchanges import Bitmex
from cryptofeed_experiments.trades import (
    SignificantTradeCallback,
    TradeCallback,
    TradeClusterCallback,
)


async def trades(trade: dict, timestamp: float) -> None:
    """Trades."""
    print(trade)


if __name__ == "__main__":
    fh = FeedHandler()
    fh.add_feed(
        Bitmex(
            symbols=["XBTUSD"],
            channels=[TRADES],
            callbacks={
                TRADES: TradeCallback(
                    SignificantTradeCallback(
                        TradeClusterCallback(trades), significant_trade_filter=1_000
                    )
                )
            },
        )
    )
    fh.run()
