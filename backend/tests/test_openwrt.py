"""OpenWrt 集成测试：用 MockTransport 模拟 ubus JSON-RPC。"""

import json
from typing import Any

import httpx
import pytest

from app.domain.capability import Capability
from app.domain.events import (
    DeviceAvailabilityEvent,
    EventBus,
    NeighborReportEvent,
)
from app.integrations.openwrt.client import UbusClient, UbusError
from app.integrations.openwrt.integration import OpenWrtIntegration
from app.plugins.catalog import EntityCatalog
from app.plugins.context import BaseIntegrationContext
from app.plugins.state_store import StateStore

BOARD = {
    "hostname": "router",
    "model": "Xiaomi AX3000T",
    "board_name": "xiaomi,ax3000t",
    "release": {
        "distribution": "OpenWrt",
        "version": "23.05.4",
        "description": "OpenWrt 23.05.4",
    },
}

INFO = {
    "uptime": 12345,
    "load": [0.5, 0.4, 0.3],
    "memory": {
        "total": 268435456,
        "free": 201326592,
        "available": 201326592,
    },
}

NETWORK = {
    "interface": [
        {
            "interface": "wan",
            "up": True,
            "proto": "dhcp",
            "ipv4-address": [{"address": "203.0.113.10", "mask": 24}],
        },
    ],
}

HINTS = {
    "aa:bb:cc:dd:ee:01": {
        "ip": "192.168.1.10",
        "name": "laptop",
    },
}

LEASES = {
    "dhcp_leases": [
        {
            "macaddr": "aa:bb:cc:dd:ee:02",
            "ipaddr": "192.168.1.11",
            "hostname": "phone",
        },
    ],
}


def _rpc(result: Any) -> httpx.Response:
    return httpx.Response(
        200,
        json={"jsonrpc": "2.0", "id": 1, "result": [0, result]},
    )


def _handler_factory(
    calls: list[tuple[str, str, dict[str, Any]]],
    *,
    fail_info: bool = False,
):
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        session, obj, method, params = payload["params"]

        calls.append((obj, method, params))

        if (obj, method) == ("session", "login"):
            assert params["username"] == "root"
            assert params["password"] == "secret"
            return _rpc({"ubus_rpc_session": "test-session"})

        if (obj, method) == ("system", "info") and fail_info:
            return httpx.Response(
                200,
                json={"jsonrpc": "2.0", "id": 1, "result": [2, "not found"]},
            )

        routes = {
            ("system", "board"): BOARD,
            ("system", "info"): INFO,
            ("network.interface", "dump"): NETWORK,
            ("network.device", "status"): {
                "macaddr": "AA:BB:CC:DD:EE:00",
            },
            ("iwinfo", "devices"): {"devices": ["wlan0"]},
            ("iwinfo", "assoclist"): {
                "results": [
                    {"mac": "aa:bb:cc:dd:ee:01", "signal": -50},
                    {"mac": "aa:bb:cc:dd:ee:02", "signal": -60},
                ],
            },
            ("luci-rpc", "getHostHints"): HINTS,
            ("luci-rpc", "getDHCPLeases"): LEASES,
        }

        result = routes.get((obj, method))

        if result is None:
            return httpx.Response(
                200,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "result": [2, "method not found"],
                },
            )

        return _rpc(result)

    return handler


def _build_integration(
    transport: httpx.AsyncBaseTransport,
    bus: EventBus,
    catalog: EntityCatalog,
    state_store: StateStore,
    instance: str,
) -> tuple[OpenWrtIntegration, BaseIntegrationContext]:
    config = {
        "host": "192.168.1.1",
        "username": "root",
        "password": "secret",
        "device_key": "main",
        "name": "客厅路由器",
    }

    context = BaseIntegrationContext(
        "openwrt",
        config,
        catalog,
        bus,
        state_store,
        instance=instance,
    )
    integration = OpenWrtIntegration(context)
    integration.client_factory = lambda _: UbusClient(
        host="192.168.1.1",
        username="root",
        password="secret",
        transport=transport,
    )

    return integration, context


async def test_openwrt_discover_poll_and_neighbors() -> None:
    calls: list[tuple[str, str, dict[str, Any]]] = []
    transport = httpx.MockTransport(_handler_factory(calls))

    bus = EventBus()
    catalog = EntityCatalog()
    state_store = StateStore()
    events: list = []

    async def collect(event) -> None:
        events.append(event)

    bus.subscribe(collect)

    integration, context = _build_integration(
        transport,
        bus,
        catalog,
        state_store,
        instance="home",
    )

    assert integration.manifest.capabilities == frozenset(
        {Capability.READONLY},
    )

    await integration.setup()

    devices = await integration.discover()
    assert len(devices) == 1

    device = await context.register_device(devices[0])
    assert device.device_id == "openwrt.home.main"
    assert device.name == "客厅路由器"
    assert device.model == "Xiaomi AX3000T"
    assert device.sw_version == "OpenWrt 23.05.4"
    assert device.identity == "mac:aa:bb:cc:dd:ee:00"

    await integration.poll()

    expected_entities = {
        "openwrt.home.main.uptime",
        "openwrt.home.main.load_1m",
        "openwrt.home.main.memory_total",
        "openwrt.home.main.memory_used",
        "openwrt.home.main.memory_usage",
        "openwrt.home.main.firmware",
        "openwrt.home.main.wan_up",
        "openwrt.home.main.wan_ip",
        "openwrt.home.main.wlan_clients",
    }
    assert expected_entities <= {entity.entity_id for entity in catalog.all_entities()}

    assert state_store.get("openwrt.home.main.uptime").value == 12345
    assert state_store.get("openwrt.home.main.load_1m").value == 0.5
    assert state_store.get("openwrt.home.main.memory_total").value == 256.0
    assert state_store.get("openwrt.home.main.memory_used").value == 64.0
    assert state_store.get("openwrt.home.main.memory_usage").value == 25.0
    assert state_store.get("openwrt.home.main.wan_up").value is True
    assert state_store.get("openwrt.home.main.wan_ip").value == "203.0.113.10"
    assert state_store.get("openwrt.home.main.wlan_clients").value == 2

    neighbor_events = [
        event for event in events if isinstance(event, NeighborReportEvent)
    ]
    assert len(neighbor_events) == 1

    neighbors = {n.mac: n for n in neighbor_events[0].neighbors}
    assert set(neighbors) == {"aa:bb:cc:dd:ee:01", "aa:bb:cc:dd:ee:02"}
    assert neighbors["aa:bb:cc:dd:ee:01"].hostname == "laptop"
    assert neighbors["aa:bb:cc:dd:ee:01"].is_wireless is True
    assert neighbors["aa:bb:cc:dd:ee:02"].hostname == "phone"

    availability = [
        event for event in events if isinstance(event, DeviceAvailabilityEvent)
    ]
    assert len(availability) == 1
    assert availability[0].available is True

    # 登录一次，后续调用复用会话
    assert calls[0] == (
        "session",
        "login",
        {"username": "root", "password": "secret", "timeout": 3600},
    )

    await integration.close()


async def test_openwrt_marks_unavailable_on_failure() -> None:
    calls: list[tuple[str, str, dict[str, Any]]] = []
    transport = httpx.MockTransport(
        _handler_factory(calls, fail_info=True),
    )

    bus = EventBus()
    catalog = EntityCatalog()
    state_store = StateStore()
    events: list = []

    async def collect(event) -> None:
        events.append(event)

    bus.subscribe(collect)

    integration, context = _build_integration(
        transport,
        bus,
        catalog,
        state_store,
        instance="failure",
    )

    await integration.setup()
    device = await context.register_device((await integration.discover())[0])

    with pytest.raises(UbusError):
        await integration.poll()

    availability = [
        event
        for event in events
        if isinstance(event, DeviceAvailabilityEvent)
        and event.device_id == device.device_id
    ]

    assert len(availability) == 1
    assert availability[0].available is False

    await integration.close()
