import os
from decimal import Decimal

from cryptofeed.backends.gcppubsub import GCPPubSubCallback
from gcloud.aio.pubsub import PublisherClient, PubsubMessage
from yapic import json

from ..constants import PROJECT_ID
from .utils import normalize_symbol


class GCPPubSubTradeCallback(GCPPubSubCallback):
    default_key = "trades"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.topics = {}

    def get_topic(self) -> str:
        # By symbol
        pass

    async def __call__(self, trade: dict) -> None:
        topic = self.get_topic_path(trade)
        message = self.get_message(trade)
        await self.write(topic, message)
        # Next callback
        await self.handler(trade)

    def get_topic_path(self, trade: dict) -> str:
        feed = trade["feed"]
        symbol = trade["symbol"]
        symbols = self.topics.setdefault(feed, {})
        return symbols.setdefault(symbol, self.set_topic_path(feed, symbol))

    def set_topic_path(self, feed: str, symbol: str) -> str:
        feed = feed.lower()
        symbol = normalize_symbol(feed, symbol)
        topic = f"{feed}-{symbol}-{self.default_key}"
        return PublisherClient.topic_path(os.getenv(PROJECT_ID), topic)

    def get_message(self, trade: dict) -> PubsubMessage:
        for key in ("feed", "symbol"):
            trade.pop(key)
        for key, value in trade.items():
            if isinstance(value, Decimal):
                trade[key] = str(value)  # B/C json returns floats
        payload = json.dumps(trade)
        return PubsubMessage(payload.encode())

    async def write(self, topic: str, message: dict) -> None:
        client = await self.get_client()
        await client.publish(topic, [message])
