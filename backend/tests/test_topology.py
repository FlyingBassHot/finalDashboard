"""拓扑测试：邻居聚合、身份匹配、图构建与清理。"""

from datetime import timedelta

from app.core.db_types import utcnow
from app.domain.device import DeviceCategory, DeviceDescriptor
from app.domain.events import EventBus, NeighborReportEvent
from app.domain.topology import Neighbor
from app.repositories.devices import DeviceRepository
from app.topology.recorder import TopologyRecorder
from app.topology.repository import NeighborLinkRepository
from app.topology.service import TopologyService

PARENT = DeviceDescriptor(
    key="main",
    name="路由器",
    category=DeviceCategory.ROUTER,
    integration="test_topo",
    instance="home",
    identity="mac:aa:aa:aa:aa:aa:01",
)

CHILD = DeviceDescriptor(
    key="nas",
    name="NAS",
    category=DeviceCategory.NAS,
    integration="test_nas",
    instance="home",
    identity="mac:bb:bb:bb:bb:bb:02",
)

NEIGHBORS = (
    Neighbor(
        mac="bb:bb:bb:bb:bb:02",
        ip="192.168.1.2",
        hostname="nas",
    ),
    Neighbor(
        mac="CC:CC:CC:CC:CC:03",
        ip="192.168.1.3",
        hostname="phone",
        interface="wlan0",
        is_wireless=True,
    ),
    # 自己：应被忽略，不产生 self-loop
    Neighbor(mac="aa:aa:aa:aa:aa:01", ip="192.168.1.1"),
)


async def _seed_devices(session_factory) -> None:
    async with session_factory() as db:
        repository = DeviceRepository()
        await repository.upsert(db, PARENT)
        await repository.upsert(db, CHILD)
        await db.commit()


async def test_topology_records_and_builds_graph(session_factory) -> None:
    await _seed_devices(session_factory)

    bus = EventBus()
    recorder = TopologyRecorder(session_factory)
    recorder.register(bus)

    observed_at = utcnow()

    await bus.publish(
        NeighborReportEvent(
            source="test_topo.home",
            device_id=PARENT.device_id,
            neighbors=NEIGHBORS,
            occurred_at=observed_at,
        ),
    )

    async with session_factory() as db:
        links = await NeighborLinkRepository().list_for_device(
            db,
            PARENT.device_id,
        )

    # MAC 统一小写；self-loop 在构图阶段过滤
    assert {link.mac for link in links} == {
        "aa:aa:aa:aa:aa:01",
        "bb:bb:bb:bb:bb:02",
        "cc:cc:cc:cc:cc:03",
    }
    assert all(link.last_seen_at.tzinfo is not None for link in links)

    async with session_factory() as db:
        graph = await TopologyService().build(
            db,
            active_within_seconds=600,
        )

    nodes = {node["id"]: node for node in graph["nodes"]}

    assert nodes[PARENT.device_id]["kind"] == "device"
    assert nodes[CHILD.device_id]["kind"] == "device"
    assert nodes[CHILD.device_id]["mac"] == "bb:bb:bb:bb:bb:02"
    assert nodes[CHILD.device_id]["ip"] == "192.168.1.2"

    unknown = nodes["mac:cc:cc:cc:cc:cc:03"]
    assert unknown["kind"] == "neighbor"
    assert unknown["hostname"] == "phone"

    edges = {(edge["source"], edge["target"]) for edge in graph["edges"]}

    assert (PARENT.device_id, CHILD.device_id) in edges
    assert (PARENT.device_id, "mac:cc:cc:cc:cc:cc:03") in edges
    assert (PARENT.device_id, PARENT.device_id) not in edges

    wireless_edge = next(
        edge for edge in graph["edges"] if edge["target"] == "mac:cc:cc:cc:cc:cc:03"
    )
    assert wireless_edge["is_wireless"] is True
    assert wireless_edge["interface"] == "wlan0"

    recorder.close()


async def test_neighbor_upsert_deduplicates_and_updates_last_seen(
    session_factory,
) -> None:
    await _seed_devices(session_factory)

    bus = EventBus()
    recorder = TopologyRecorder(session_factory)
    recorder.register(bus)

    first = utcnow()
    second = first + timedelta(minutes=5)

    await bus.publish(
        NeighborReportEvent(
            device_id=PARENT.device_id,
            neighbors=(Neighbor(mac="bb:bb:bb:bb:bb:02", ip="192.168.1.2"),),
            occurred_at=first,
        ),
    )
    await bus.publish(
        NeighborReportEvent(
            device_id=PARENT.device_id,
            neighbors=(Neighbor(mac="BB:BB:BB:BB:BB:02", ip="192.168.1.20"),),
            occurred_at=second,
        ),
    )

    async with session_factory() as db:
        links = await NeighborLinkRepository().list_for_device(
            db,
            PARENT.device_id,
        )

    assert len(links) == 1
    assert links[0].mac == "bb:bb:bb:bb:bb:02"
    assert links[0].ip == "192.168.1.20"
    assert links[0].first_seen_at == first
    assert links[0].last_seen_at == second

    recorder.close()


async def test_neighbor_active_window_and_cleanup(session_factory) -> None:
    await _seed_devices(session_factory)

    bus = EventBus()
    recorder = TopologyRecorder(session_factory)
    recorder.register(bus)

    observed_at = utcnow()

    await bus.publish(
        NeighborReportEvent(
            device_id=PARENT.device_id,
            neighbors=(Neighbor(mac="bb:bb:bb:bb:bb:02", ip="192.168.1.2"),),
            occurred_at=observed_at,
        ),
    )

    repository = NeighborLinkRepository()

    async with session_factory() as db:
        active = await repository.list_active(
            db,
            observed_at - timedelta(seconds=1),
        )
        stale = await repository.list_active(
            db,
            observed_at + timedelta(seconds=1),
        )

        assert len(active) == 1
        assert stale == []

        deleted = await repository.delete_stale(
            db,
            observed_at + timedelta(seconds=1),
        )
        await db.commit()

        remaining = await repository.list_active(
            db,
            observed_at - timedelta(days=1),
        )

    assert deleted == 1
    assert remaining == []

    recorder.close()
