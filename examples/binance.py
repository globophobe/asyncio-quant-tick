#!/usr/bin/env python3
from cryptofeed import FeedHandler
from cryptofeed.defines import TRADES

from cryptofeed_experiments.exchanges import Binance
from cryptofeed_experiments.trades import (
    SequentialIntegerTradeCallback,
    SignificantTradeCallback,
    TradeClusterCallback,
)


async def trades(trade: dict, timestamp: float) -> None:
    """Trades."""
    print(trade)


if __name__ == "__main__":
    fh = FeedHandler()
    fh.add_feed(
        Binance(
            symbols=["BTCUSDT"],
            channels=[TRADES],
            callbacks={
                TRADES: SequentialIntegerTradeCallback(
                    SignificantTradeCallback(
                        TradeClusterCallback(trades), significant_trade_filter=1_000
                    )
                )
            },
        )
    )
    fh.run()
