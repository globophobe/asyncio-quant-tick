#!/usr/bin/env python3

from cryptofeed import FeedHandler
from cryptofeed.defines import TRADES
from cryptofeed_werks.exchanges import Binance
from cryptofeed_werks.trades import SignificantTradeCallback, TradeCallback


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
                TRADES: TradeCallback(
                    SignificantTradeCallback(
                        trades,
                        significant_trade_filter=100_000,  # Volume is high
                        window_seconds=60,
                    )
                )
            },
        )
    )
    fh.run()
