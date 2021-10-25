import os
from uuid import uuid4

from cryptofeed.backends.aggregate import AggregateCallback
from google.cloud.firestore import AsyncClient

from ..constants import FIREBASE_ADMIN_CREDENTIALS
from ..utils import is_local, set_environment
from .utils import decimal_to_str, normalize_symbol


class FirestoreTradeCallback(AggregateCallback):
    def __init__(self, *args, key="trades", **kwargs):
        super().__init__(*args, **kwargs)
        self.key = key

    def get_client(self):
        if not hasattr(self, "client"):
            self.client = AsyncClient()
            if is_local():
                set_environment()
                credentials = os.environ[FIREBASE_ADMIN_CREDENTIALS]
                self.client.from_service_account_json(credentials)
        return self.client

    async def __call__(self, data: dict):
        feed = data.pop("feed")
        symbol = data.pop("symbol")
        collection = self.get_collection(feed, symbol)
        await self.set_document(collection, data)

    def get_collection(self, feed: str, symbol: str):
        feed = feed.lower()
        symbol = normalize_symbol(feed, symbol)
        return f"{feed}-{symbol}-{self.key}"

    async def set_document(self, collection, data):
        client = self.get_client()
        # Uuid document ID all the time
        # https://firebase.google.com/docs/firestore/best-practices#document_ids
        document = uuid4().hex
        decimal_to_str(data)
        await client.collection(collection).document(document).set(data)
