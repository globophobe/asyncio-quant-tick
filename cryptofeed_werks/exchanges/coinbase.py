from decimal import Decimal

from cryptofeed.defines import ASK, BID, L3_BOOK, TRADES
from cryptofeed.exchanges import Coinbase


class CoinbaseExchange(Coinbase):
    async def _book_update(self, msg: dict, timestamp: float):
        """
        {
            'type': 'match', or last_match
            'trade_id': 43736593
            'maker_order_id': '2663b65f-b74e-4513-909d-975e3910cf22',
            'taker_order_id': 'd058d737-87f1-4763-bbb4-c2ccf2a40bde',
            'side': 'buy',
            'size': '0.01235647',
            'price': '8506.26000000',
            'product_id': 'BTC-USD',
            'sequence': 5928276661,
            'time': '2018-05-21T00:26:05.585000Z'
        }
        """
        pair = msg["product_id"]
        ts = self.timestamp_normalize(msg["time"])

        if self.keep_l3_book and (
            "full" in self.channels
            or ("full" in self.subscription and pair in self.subscription["full"])
        ):
            delta = {BID: [], ASK: []}
            price = Decimal(msg["price"])
            side = ASK if msg["side"] == "sell" else BID
            size = Decimal(msg["size"])
            maker_order_id = msg["maker_order_id"]

            _, new_size = self.order_map[maker_order_id]
            new_size -= size
            if new_size <= 0:
                del self.order_map[maker_order_id]
                self.order_type_map.pop(maker_order_id, None)
                delta[side].append((maker_order_id, price, 0))
                del self.l3_book[pair][side][price][maker_order_id]
                if len(self.l3_book[pair][side][price]) == 0:
                    del self.l3_book[pair][side][price]
            else:
                self.order_map[maker_order_id] = (price, new_size)
                self.l3_book[pair][side][price][maker_order_id] = new_size
                delta[side].append((maker_order_id, price, new_size))

            await self.book_callback(
                self.l3_book[pair], L3_BOOK, pair, False, delta, ts, timestamp
            )

        price = Decimal(msg["price"])
        notional = Decimal(msg["size"])
        volume = price * notional
        await self.callback(
            TRADES,
            feed=self.id,
            uid=int(msg["trade_id"]),
            symbol=msg["product_id"],  # Do not normalize
            timestamp=ts,
            price=price,
            volume=volume,
            notional=notional,
            tickRule=1 if msg["side"] == "sell" else -1,
        )
