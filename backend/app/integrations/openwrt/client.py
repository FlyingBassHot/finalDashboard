"""OpenWrt ubus/rpcd JSON-RPC 客户端。

只使用固件自带的 rpcd HTTP 端点（无侵入），不做任何配置下发。
"""

import itertools
from typing import Any

import httpx

from app.plugins.errors import IntegrationError

ANONYMOUS_SESSION = "00000000000000000000000000000000"


class UbusError(IntegrationError):
    """ubus 调用失败（网络、认证或方法返回非 0）。"""


class UbusClient:
    def __init__(
        self,
        host: str,
        *,
        scheme: str = "http",
        username: str = "",
        password: str = "",
        verify_tls: bool = True,
        timeout: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        base = host if "://" in host else f"{scheme}://{host}"

        self._url = f"{base.rstrip('/')}/ubus"
        self._username = username
        self._password = password
        self._session = ANONYMOUS_SESSION
        self._ids = itertools.count(1)
        self._client = httpx.AsyncClient(
            timeout=timeout,
            verify=verify_tls,
            transport=transport,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def login(self) -> None:
        if not self._username:
            return

        result = await self._call_raw(
            "session",
            "login",
            {
                "username": self._username,
                "password": self._password,
                "timeout": 3600,
            },
        )

        session = result.get("ubus_rpc_session")

        if not session:
            raise UbusError("ubus login succeeded but no session returned")

        self._session = str(session)

    async def call(
        self,
        obj: str,
        method: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = await self._call_raw(obj, method, params or {})

        return result if isinstance(result, dict) else {}

    async def _call_raw(
        self,
        obj: str,
        method: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        payload = {
            "jsonrpc": "2.0",
            "id": next(self._ids),
            "method": "call",
            "params": [self._session, obj, method, params],
        }

        try:
            response = await self._client.post(self._url, json=payload)
            response.raise_for_status()
            data = response.json()

        except (httpx.HTTPError, ValueError) as exc:
            raise UbusError(f"ubus request failed: {exc}") from exc

        if data.get("error") is not None:
            raise UbusError(f"ubus rpc error: {data['error']}")

        result = data.get("result")

        if not isinstance(result, list) or not result:
            raise UbusError("ubus returned invalid result")

        code = result[0]

        if code != 0:
            detail = result[1] if len(result) > 1 else code
            raise UbusError(f"{obj}.{method} failed: {detail}")

        return result[1] if len(result) > 1 and isinstance(result[1], dict) else {}
