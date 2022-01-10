# What?

This is the basis of a pipeline for live data from cryptocurrency exchanges. It normalizes [cryptofeed](https://github.com/bmoscon/cryptofeed) WebSocket messages, aggregates, and optionally publishes them to GCP Pub/Sub.

# How?

Sequences of trades that have equal symbol, timestamp, nanoseconds, and tick rule are aggregated. Aggregating trades in this way can increase information, as they are either orders of size or stop loss cascades.

As well, the number of messages can be reduced by 30-50%

By filtering aggregated messages, for example only emitting a mesage when an aggregated trade is greater than `min_volume`, the number of messages can be reduced more.

Example
-------
The following are two sequential aggregated trades by timestamp, nanoseconds, and tick rule.

As it was aggregated from 4 raw trades, the second trade has ticks 4.

```python
[
    {
        "timestamp": 1620000915.31424,
        "price": "57064.01",
        "volume": "566.6479018604",
        "notional": "0.00993004",
        "tickRule": -1,
        "ticks": 1
    },
    {
        "timestamp": 1620000915.885381,
        "price": "57071.2",
        "volume": "9376.6869202914",
        "notional": "0.16429813",
        "tickRule": 1,
        "ticks": 4
    }
]
```

An example filtered message, emitted because the second aggregated trade exceeds `min_volume >= 1000`

Information related to the first trade is aggregated with the second.

```python
[
    {
        "timestamp": 1620000915.885381,
        "price": "57071.2",
        "volume": "9376.6869202914",
        "notional": "0.16429813",
        "tickRule": 1,
        "ticks": 4,
        "high": '57071.2',
        "low": '57064.01',
        "totalBuyVolume": "9376.6869202914",
        "totalVolume": "9943.3348221518",
        "totalBuyNotional": "0.16429813",
        "totalNotional": "0.17422817",
        "totalBuyTicks": 4,
        "totalTicks": 5
    }
]
```

For 1m, 5m, 15m candles, there is an optional parameter `window_seconds`.  

For settings, see [demo.py](https://github.com/globophobe/cryptofeed-werks/blob/main/demo.py)

Supported exchanges
-------------------

:white_check_mark: Binance
:white_check_mark: Bitfinex
:white_check_mark: Bitflyer
:white_check_mark: BitMEX
:white_check_mark: Bybit
:white_check_mark: Coinbase Pro
:white_check_mark: Deribit
:white_check_mark: FTX
:white_check_mark: Upbit

Contributing
------------

Install dependencies with `poetry install`. The demo is built with [invoke tasks](https://github.com/globophobe/cryptofeed-werks/blob/master/tasks.py). For example, `invoke build`

Future plans
------------
Order book aggregation, in the manner of [crypto-whale-watching-app](https://github.com/pmaji/crypto-whale-watching-app)
