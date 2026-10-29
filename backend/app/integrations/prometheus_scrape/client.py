"""Prometheus 文本端点的 HTTP 客户端（只读 GET）。"""

import httpx

from app.plugins.errors import IntegrationError


class ExporterError(IntegrationError):
    """抓取 exporter 失败（网络、HTTP 状态或报文格式）。"""


class ExporterClient:
    def __init__(
        self,
        url: str,
        *,
        verify_tls: bool = True,
        timeout: float = 10.0,
        bearer_token: str = "",
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        headers = {"Accept": "text/plain"}

        if bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"

        self._url = url
        self._client = httpx.AsyncClient(
            timeout=timeout,
            verify=verify_tls,
            headers=headers,
            transport=transport,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def fetch(self) -> str:
        try:
            response = await self._client.get(self._url)
            response.raise_for_status()

        except httpx.HTTPError as exc:
            raise ExporterError(f"scrape failed: {exc}") from exc

        return response.text
