from cryptofeed.defines import TRADES
from cryptofeed.exchanges import Bitflyer
from cryptofeed.standards import timestamp_normalize


class BitflyerBlotter(Bitflyer):
    async def _trade(self, msg: dict, timestamp: float):
        """
        {
            "jsonrpc":"2.0",
            "method":"channelMessage",
            "params":{
                "channel":"lightning_executions_BTC_JPY",
                "message":[
                    {
                        "id":2084881071,
                        "side":"BUY",
                        "price":2509125.0,
                        "size":0.005,
                        "exec_date":"2020-12-25T21:36:22.8840579Z",
                        "buy_child_order_acceptance_id":"JRF20201225-213620-004123",
                        "sell_child_order_acceptance_id":"JRF20201225-213620-133314"
                    }
                ]
            }
        }
        """
        pair = msg["params"]["channel"][21:]
        for update in msg["params"]["message"]:
            price = update["price"]
            notional = update["size"]
            volume = price * notional
            await self.callback(
                TRADES,
                feed=self.id,
                uid=update["id"],
                symbol=pair,  # Do not normalize
                timestamp=timestamp_normalize(self.id, update["exec_date"]),
                price=price,
                volume=volume,
                notional=notional,
                tickRule=1 if update["side"] == "BUY" else -1,
            )
