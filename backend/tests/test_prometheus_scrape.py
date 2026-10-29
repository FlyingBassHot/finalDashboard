"""prometheus_scrape 集成测试：固定 exporter 报文 + MockTransport。"""

import httpx
import pytest

from app.domain.capability import Capability
from app.domain.events import DeviceAvailabilityEvent, EventBus
from app.integrations.prometheus_scrape.client import (
    ExporterClient,
    ExporterError,
)
from app.integrations.prometheus_scrape.integration import (
    PrometheusScrapeIntegration,
)
from app.integrations.prometheus_scrape.mapping import (
    build_readings,
    parse_exposition,
)
from app.plugins.catalog import EntityCatalog
from app.plugins.context import BaseIntegrationContext
from app.plugins.contract import PollingIntegration
from app.plugins.errors import IntegrationConfigError
from app.plugins.state_store import StateStore

EXPOSITION = """\
# HELP node_load1 1m load average.
# TYPE node_load1 gauge
node_load1 0.52
# HELP node_memory_MemTotal_bytes Memory information field MemTotal_bytes.
# TYPE node_memory_MemTotal_bytes gauge
node_memory_MemTotal_bytes 268435456
node_memory_MemAvailable_bytes 201326592
node_boot_time_seconds 1793000000
node_time_seconds 1793100000
node_filesystem_size_bytes{device="tmpfs",fstype="tmpfs",mountpoint="/run"} 100000000
node_filesystem_size_bytes{device="/dev/sda1",fstype="ext4",mountpoint="/"} 10737418240
node_filesystem_avail_bytes{device="/dev/sda1",fstype="ext4",mountpoint="/"} 5368709120
node_os_info{id="ubuntu",name="Ubuntu \\"Server\\"",version="24.04 LTS"} 1
node_cpu_seconds_total{cpu="0",mode="idle"} 12345.6
"""

CONFIG = {
    "url": "http://192.168.1.20:9100/metrics",
    "device_key": "main",
    "name": "NAS-01",
    "mac": "AA:BB:CC:DD:EE:10",
    "category": "nas",
}


def _integration(
    body: str | None,
    *,
    status: int = 200,
    config: dict | None = None,
):
    def handler(request: httpx.Request) -> httpx.Response:
        if body is None:
            return httpx.Response(status, text="internal error")

        return httpx.Response(status, text=body)

    transport = httpx.MockTransport(handler)

    bus = EventBus()
    catalog = EntityCatalog()
    state_store = StateStore()
    events: list = []

    async def collect(event) -> None:
        events.append(event)

    bus.subscribe(collect)

    context = BaseIntegrationContext(
        "prometheus_scrape",
        config or CONFIG,
        catalog,
        bus,
        state_store,
        instance="home",
    )
    integration = PrometheusScrapeIntegration(context)
    integration.client_factory = lambda cfg: ExporterClient(
        cfg["url"],
        transport=transport,
    )

    return integration, context, catalog, state_store, events


def test_manifest_is_readonly_polling() -> None:
    assert issubclass(PrometheusScrapeIntegration, PollingIntegration)
    assert PrometheusScrapeIntegration.manifest.capabilities == frozenset(
        {Capability.READONLY},
    )


async def test_scrape_maps_node_exporter_metrics() -> None:
    integration, context, catalog, state_store, events = _integration(
        EXPOSITION,
    )

    await integration.setup()

    devices = await integration.discover()
    device = await context.register_device(devices[0])

    assert device.device_id == "prometheus_scrape.home.main"
    assert device.name == "NAS-01"
    assert device.identity == "mac:aa:bb:cc:dd:ee:10"

    await integration.poll()

    def value(key: str):
        state = state_store.get(f"prometheus_scrape.home.main.{key}")
        assert state is not None, key
        return state.value

    assert value("load_1m") == 0.52
    assert value("uptime") == 100000
    assert value("memory_total") == 256.0
    assert value("memory_used") == 64.0
    assert value("memory_usage") == 25.0
    assert value("disk_total") == 10240.0
    assert value("disk_usage") == 50.0
    assert value("os_version") == 'Ubuntu "Server" 24.04 LTS'

    unit = catalog.find_entity("prometheus_scrape.home.main.memory_usage").unit
    assert unit == "%"

    availability = [
        event for event in events if isinstance(event, DeviceAvailabilityEvent)
    ]
    assert availability[-1].available is True

    await integration.close()


async def test_missing_metrics_are_skipped() -> None:
    integration, context, catalog, state_store, _ = _integration(
        "node_load1 1.5\n",
    )

    await integration.setup()
    await context.register_device((await integration.discover())[0])
    await integration.poll()

    keys = {entity.key for entity in catalog.all_entities()}

    assert keys == {"load_1m"}
    assert state_store.get("prometheus_scrape.home.main.load_1m").value == 1.5

    await integration.close()


async def test_http_error_marks_unavailable_and_raises() -> None:
    integration, context, _, _, events = _integration(None, status=500)

    await integration.setup()
    device = await context.register_device((await integration.discover())[0])

    with pytest.raises(ExporterError):
        await integration.poll()

    availability = [
        event
        for event in events
        if isinstance(event, DeviceAvailabilityEvent)
        and event.device_id == device.device_id
    ]

    assert availability[-1].available is False

    await integration.close()


async def test_invalid_url_is_a_config_error() -> None:
    integration, _, _, _, _ = _integration(
        EXPOSITION,
        config={"url": "192.168.1.20:9100/metrics"},
    )

    with pytest.raises(IntegrationConfigError):
        await integration.setup()


async def test_invalid_mac_and_category_are_config_errors() -> None:
    integration, _, _, _, _ = _integration(
        EXPOSITION,
        config={**CONFIG, "mac": "not-a-mac"},
    )

    await integration.setup()

    with pytest.raises(IntegrationConfigError):
        await integration.discover()

    integration, _, _, _, _ = _integration(
        EXPOSITION,
        config={**CONFIG, "category": "router"},
    )

    await integration.setup()

    with pytest.raises(IntegrationConfigError):
        await integration.discover()


def test_parser_handles_escapes_and_nan() -> None:
    index = parse_exposition(
        'node_load1 NaN\nnode_os_info{name="a\\"b"} 1\n',
    )

    readings = {reading.key: reading.value for reading in build_readings(index)}

    assert "load_1m" not in readings
    assert readings["os_version"] == 'a"b'
