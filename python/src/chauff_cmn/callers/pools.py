from ..models import PoolStats, PoolApiDataPayload, PoolDistributionElement
from aiohttp import ClientSession


class PoolAPIClient:
    session: ClientSession | None = None

    def __init__(self, api_url: str, api_key: str):
        self._api_url = api_url
        self._api_key = api_key

    def _get_session(self) -> ClientSession:
        if self.session is None:
            self.session = ClientSession(self._api_url)
        return self.session

    async def _get(self, url: str):
        async with self._get_session() as session:
            async with session.get(url) as response:
                return await response.json()

    async def _authenticated_get(self, url: str):
        async with self._get_session() as session:
            async with session.get(url, headers = {"Authorization": f"Bearer {self._api_key}"}) as response:
                return await response.json()

    async def get_pool_stats(self, address: str) -> PoolStats:
        return PoolStats(**await self._get(f"/v1/stats/{address}"))

    async def get_pool_share_distribution(self, address: str) -> PoolDistributionElement:
        return PoolDistributionElement(**await self._get(f"/v1/share_distribution/{address}"))

    async def get_cluster(self):
        return PoolApiDataPayload(**await self._authenticated_get("/v1/data"))
