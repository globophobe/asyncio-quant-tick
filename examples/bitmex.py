#!/usr/bin/env python3

from cryptofeed import FeedHandler
from cryptofeed.defines import TRADES
from cryptofeed_werks.exchanges import Bitmex
from cryptofeed_werks.trades import SignificantTradeCallback, TradeCallback


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
                        trades, significant_trade_filter=1_000, window_seconds=60
                    )
                )
            },
        )
    )
    fh.run()
