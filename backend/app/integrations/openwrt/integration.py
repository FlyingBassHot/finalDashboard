"""OpenWrt 集成（P0 · 第一类 · 只读）。

通过固件自带的 ubus / rpcd JSON-RPC 采集系统、接口与无线客户端信息，
并上报邻居表供拓扑使用。不通过 ubus 下发任何配置。
"""

import re
from collections.abc import Callable, Mapping
from typing import Any

from app.domain.capability import Capability
from app.domain.device import DeviceCategory, DeviceDescriptor
from app.domain.entity import EntityDescriptor
from app.domain.state import EntityState
from app.domain.topology import Neighbor
from app.integrations.openwrt.client import UbusClient, UbusError
from app.plugins.contract import PollingIntegration
from app.plugins.errors import IntegrationConfigError
from app.plugins.manifest import IntegrationManifest
from app.plugins.registry import register_integration

MAC_PATTERN = re.compile(r"[0-9a-f]{2}(:[0-9a-f]{2}){5}")
DEVICE_KEY_PATTERN = re.compile(r"[A-Za-z0-9_-]+")
MIB = 1024 * 1024


def _as_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "on"}

    return default


def _valid_mac(value: str) -> bool:
    return bool(MAC_PATTERN.fullmatch(value.lower()))


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


@register_integration
class OpenWrtIntegration(PollingIntegration):
    manifest = IntegrationManifest(
        name="openwrt",
        display_name="OpenWrt 路由器",
        description=(
            "通过 ubus / rpcd JSON-RPC 只读采集系统、接口与无线客户端，"
            "并上报邻居表供拓扑使用。"
        ),
        capabilities=frozenset({Capability.READONLY}),
        supported_categories=frozenset(
            {DeviceCategory.ROUTER, DeviceCategory.GATEWAY},
        ),
        default_poll_interval_seconds=60,
        requires_credentials=True,
    )

    def __init__(self, context) -> None:
        super().__init__(context)

        self._client: UbusClient | None = None
        self._device: DeviceDescriptor | None = None
        self._device_key = "main"
        self._board: dict[str, Any] = {}
        self._wireless: list[dict[str, Any]] = []

        self.client_factory: Callable[[Mapping[str, Any]], UbusClient] = (
            self._default_client_factory
        )

    def _default_client_factory(
        self,
        config: Mapping[str, Any],
    ) -> UbusClient:
        return UbusClient(
            host=str(config.get("host", "")).strip(),
            scheme=str(config.get("scheme", "http")),
            username=str(config.get("username", "")),
            password=str(config.get("password", "")),
            verify_tls=_as_bool(config.get("verify_tls"), True),
            timeout=float(config.get("timeout", 10.0)),
        )

    async def setup(self) -> None:
        config = self.context.config
        host = str(config.get("host", "")).strip()

        if not host:
            raise IntegrationConfigError(
                "openwrt 集成需要配置 host（路由器地址）",
            )

        device_key = str(config.get("device_key", "main"))

        if not DEVICE_KEY_PATTERN.fullmatch(device_key):
            raise IntegrationConfigError(
                f"非法 device_key: {device_key!r}",
            )

        self._device_key = device_key
        self._client = self.client_factory(config)

        await self._client.login()

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()

    async def discover(self) -> list[DeviceDescriptor]:
        assert self._client is not None

        board = await self._client.call("system", "board")
        self._board = board

        config = self.context.config
        hostname = str(
            board.get("hostname")
            or config.get("name")
            or config.get("host")
            or "openwrt",
        )

        release = _as_dict(board.get("release"))

        device = DeviceDescriptor(
            key=self._device_key,
            name=str(config.get("name") or hostname),
            category=DeviceCategory.ROUTER,
            manufacturer="OpenWrt",
            model=board.get("model") or board.get("board_name"),
            sw_version=(release.get("description") or release.get("version")),
            identity=await self._read_identity(),
        )

        self._device = device

        return [device]

    async def _read_identity(self) -> str | None:
        """读取 LAN 网桥 MAC，作为拓扑匹配用的稳定标识。"""

        for interface in ("br-lan", "lan"):
            status = await self._optional(
                "network.device",
                "status",
                {"name": interface},
            )

            if not status:
                continue

            mac = str(status.get("macaddr") or "").lower()

            if _valid_mac(mac):
                return f"mac:{mac}"

        return None

    async def poll(self) -> None:
        assert self._client is not None
        assert self._device is not None

        try:
            info = await self._client.call("system", "info")
            await self._emit_system(info)
            await self._emit_board()

            network = await self._client.call(
                "network.interface",
                "dump",
            )
            await self._emit_network(network)

            await self._emit_wireless()

            neighbors = await self._collect_neighbors()

            if neighbors:
                await self.context.report_neighbors(
                    self._device,
                    neighbors,
                )

            await self.context.emit_device_availability(
                self._device,
                True,
            )

        except Exception:
            await self.context.emit_device_availability(
                self._device,
                False,
            )
            raise

    async def _emit_system(self, info: dict[str, Any]) -> None:
        uptime = info.get("uptime")

        if isinstance(uptime, (int, float)):
            await self._emit(
                "uptime",
                "运行时长",
                int(uptime),
                unit="s",
            )

        load = _as_list(info.get("load"))

        if load and isinstance(load[0], (int, float)):
            await self._emit(
                "load_1m",
                "1 分钟负载",
                round(float(load[0]), 2),
            )

        memory = _as_dict(info.get("memory"))
        total = float(memory.get("total") or 0)

        if total <= 0:
            return

        available = memory.get("available")
        free = float(
            available if available is not None else memory.get("free") or 0,
        )
        used = max(0.0, total - free)

        await self._emit(
            "memory_total",
            "内存总量",
            round(total / MIB, 1),
            unit="MB",
        )
        await self._emit(
            "memory_used",
            "内存占用",
            round(used / MIB, 1),
            unit="MB",
        )
        await self._emit(
            "memory_usage",
            "内存使用率",
            round(used / total * 100, 1),
            unit="%",
        )

    async def _emit_board(self) -> None:
        release = _as_dict(self._board.get("release"))
        firmware = release.get("description") or release.get("version")

        if firmware:
            await self._emit(
                "firmware",
                "固件版本",
                str(firmware),
            )

    async def _emit_network(self, data: dict[str, Any]) -> None:
        interfaces = _as_list(data.get("interface"))
        wan = next(
            (
                item
                for item in interfaces
                if isinstance(item, dict) and item.get("interface") == "wan"
            ),
            None,
        )

        if wan is None:
            return

        await self._emit(
            "wan_up",
            "WAN 连接",
            bool(wan.get("up")),
            domain="binary_sensor",
        )

        ipv4 = _as_list(wan.get("ipv4-address"))
        address = ""

        if ipv4 and isinstance(ipv4[0], dict):
            address = ipv4[0].get("address") or ""

        await self._emit(
            "wan_ip",
            "WAN IP",
            str(address),
            icon="network",
        )

    async def _emit_wireless(self) -> None:
        devices = _as_list(
            (await self._optional("iwinfo", "devices") or {}).get(
                "devices",
            ),
        )

        if not devices:
            self._wireless = []
            return

        clients: list[dict[str, Any]] = []

        for device in devices:
            assoc = await self._optional(
                "iwinfo",
                "assoclist",
                {"device": str(device)},
            )

            if not assoc:
                continue

            entries = _as_list(
                assoc.get("results") or assoc.get("assoclist"),
            )

            for entry in entries:
                if not isinstance(entry, dict):
                    continue

                mac = str(entry.get("mac", "")).lower()

                if not _valid_mac(mac):
                    continue

                clients.append(
                    {
                        "mac": mac,
                        "interface": str(device),
                        "signal": entry.get("signal"),
                    },
                )

        self._wireless = clients

        await self._emit(
            "wlan_clients",
            "无线客户端",
            len(clients),
            unit="个",
        )

    async def _collect_neighbors(self) -> list[Neighbor]:
        entries: dict[str, dict[str, Any]] = {}

        hints = await self._optional("luci-rpc", "getHostHints") or {}
        hint_items = hints.get("host_hints") if isinstance(hints, dict) else None

        if not isinstance(hint_items, dict):
            hint_items = hints

        if isinstance(hint_items, dict):
            for mac, info in hint_items.items():
                mac = str(mac).lower()

                if not _valid_mac(mac):
                    continue

                if not isinstance(info, dict):
                    continue

                entry = entries.setdefault(mac, {"mac": mac})
                entry["ip"] = info.get("ip") or info.get("ipv4") or entry.get("ip")
                entry["hostname"] = info.get("name") or entry.get("hostname")

        leases = await self._optional("luci-rpc", "getDHCPLeases") or {}
        lease_items = leases.get("dhcp_leases") if isinstance(leases, dict) else leases

        for lease in _as_list(lease_items):
            if not isinstance(lease, dict):
                continue

            mac = str(lease.get("macaddr") or lease.get("mac") or "").lower()

            if not _valid_mac(mac):
                continue

            entry = entries.setdefault(mac, {"mac": mac})
            entry["ip"] = lease.get("ipaddr") or lease.get("ip") or entry.get("ip")
            entry["hostname"] = lease.get("hostname") or entry.get("hostname")

        for client in self._wireless:
            entry = entries.setdefault(client["mac"], {"mac": client["mac"]})
            entry["interface"] = client["interface"]
            entry["is_wireless"] = True
            entry["source"] = "iwinfo"

        return [
            Neighbor(
                mac=entry["mac"],
                ip=entry.get("ip"),
                hostname=entry.get("hostname"),
                interface=entry.get("interface"),
                source=str(entry.get("source", "luci-rpc")),
                is_wireless=bool(entry.get("is_wireless")),
            )
            for entry in entries.values()
        ]

    async def _emit(
        self,
        key: str,
        name: str,
        value: Any,
        *,
        domain: str = "sensor",
        unit: str | None = None,
        icon: str | None = None,
        **attributes: Any,
    ) -> None:
        assert self._device is not None

        entity = await self.context.register_entity(
            EntityDescriptor(
                key=key,
                name=name,
                domain=domain,
                device_key=self._device.key,
                unit=unit,
                icon=icon,
            ),
        )

        await self.context.emit_state(
            entity,
            EntityState(value=value, attributes=attributes),
        )

    async def _optional(
        self,
        obj: str,
        method: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        assert self._client is not None

        try:
            return await self._client.call(obj, method, params or {})

        except UbusError:
            self.context.logger.debug(
                "optional ubus call failed: %s.%s",
                obj,
                method,
                exc_info=True,
            )
            return None
