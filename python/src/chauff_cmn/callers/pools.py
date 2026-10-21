from ..models import PoolStats, PoolApiDataPayload, PoolDistributionElement
from aiohttp import ClientSession, ClientTimeout


class PoolAPIClient:
    def __init__(self, api_url: str, api_key: str):
        self._api_url = api_url
        self._api_key = api_key
        self._session: ClientSession | None = None

    def _get_session(self) -> ClientSession:
        # la session est partagée entre les appels : on la recrée seulement si elle a été fermée
        if self._session is None or self._session.closed:
            self._session = ClientSession(self._api_url, timeout=ClientTimeout(total=30))
        return self._session

    async def close(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()
        self._session = None

    async def __aenter__(self) -> "PoolAPIClient":
        return self

    async def __aexit__(self, *exc) -> None:
        await self.close()

    async def _get(self, url: str):
        async with self._get_session().get(url) as response:
            response.raise_for_status()
            return await response.json()

    async def _authenticated_get(self, url: str):
        headers = {"Authorization": f"Bearer {self._api_key}"}
        async with self._get_session().get(url, headers=headers) as response:
            response.raise_for_status()
            return await response.json()

    async def get_pool_stats(self, address: str) -> PoolStats:
        return PoolStats(**await self._get(f"/v1/stats/{address}"))

    async def get_pool_share_distribution(self, address: str) -> PoolDistributionElement:
        return PoolDistributionElement(**await self._get(f"/v1/share_distribution/{address}"))

    async def get_cluster(self):
        return PoolApiDataPayload(**await self._authenticated_get("/v1/data"))
