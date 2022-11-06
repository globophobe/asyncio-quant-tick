#!/usr/bin/env python3

from cryptofeed import FeedHandler
from cryptofeed.defines import TRADES
from cryptofeed_werks.exchanges import Bitflyer
from cryptofeed_werks.trades import (
    NonSequentialIntegerTradeCallback,
    SignificantTradeCallback,
)


async def trades(trade: dict, timestamp: float) -> None:
    """Trades."""
    print(trade)


if __name__ == "__main__":
    fh = FeedHandler()
    fh.add_feed(
        Bitflyer(
            symbols=["BTC/JPY"],
            channels=[TRADES],
            callbacks={
                TRADES: NonSequentialIntegerTradeCallback(
                    SignificantTradeCallback(
                        trades,
                        significant_trade_filter=10_000,  # Volume is low
                        window_seconds=60,
                    )
                )
            },
        )
    )
    fh.run()
