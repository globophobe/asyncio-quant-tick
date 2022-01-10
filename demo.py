#!/usr/bin/env python3

from cryptofeed import FeedHandler
from cryptofeed.defines import TRADES

from cryptofeed_werks.exchanges import CoinbaseExchange
from cryptofeed_werks.trades import MinVolumeCallback, SequentialIntegerTradeCallback


async def trades(trade):
    print(trade)


if __name__ == "__main__":
    fh = FeedHandler()
    fh.add_feed(
        CoinbaseExchange(
            symbols=["BTC-USD"],
            channels=[TRADES],
            callbacks={
                TRADES: SequentialIntegerTradeCallback(
                    MinVolumeCallback(
                        trades,
                        min_volume=1000,
                        window_seconds=60,
                    )
                )
            },
        )
    )
    fh.run()
