"""动作执行 API 与持久化审计测试。"""

from typing import Any

import httpx
from fastapi import FastAPI

from app.api.actions import router as actions_router
from app.core.database import get_db
from app.domain.capability import Capability
from app.domain.device import DeviceDescriptor
from app.domain.entity import EntityDescriptor
from app.plugins import (
    ActionResult,
    Integration,
    IntegrationManifest,
    IntegrationRegistry,
    UnsupportedActionError,
)
from app.plugins.runtime import Runtime
from app.repositories.action_audits import ActionAuditRepository
from app.repositories.integration_instances import (
    IntegrationInstanceRepository,
)


class FakeActionIntegration(Integration):
    manifest = IntegrationManifest(
        name="fake_action",
        display_name="动作测试集成",
        capabilities=frozenset({Capability.ON_OFF}),
        default_poll_interval_seconds=60,
    )

    async def discover(self) -> list[DeviceDescriptor]:
        # 实体在 discover 中注册，测试无需等待轮询
        await self.context.register_entity(
            EntityDescriptor(
                key="switch",
                name="测试开关",
                domain="switch",
                device_key="dev",
                capabilities=frozenset({Capability.ON_OFF}),
            ),
        )

        return [DeviceDescriptor(key="dev", name="测试设备")]

    async def execute_action(self, request) -> ActionResult:
        if request.action != "turn_on":
            raise UnsupportedActionError("unknown action")

        return ActionResult(ok=True, message="turned on")


class FakeScheduler:
    def __init__(self) -> None:
        self.jobs: dict[str, Any] = {}

    def add_job(self, func: Any, trigger: Any, **kwargs: Any) -> None:
        self.jobs[kwargs["id"]] = func

    def remove_job(self, job_id: str) -> None:
        self.jobs.pop(job_id, None)


async def _build_app(session_factory):
    registry = IntegrationRegistry()
    registry.register(FakeActionIntegration)
    runtime = Runtime(session_factory, FakeScheduler(), registry=registry)

    async with session_factory() as db:
        await IntegrationInstanceRepository().create(
            db,
            name="action-home",
            integration="fake_action",
            display_name="动作实例",
            config={},
            poll_interval_seconds=60,
            enabled=True,
        )

    await runtime.startup()

    app = FastAPI()
    app.state.runtime = runtime
    app.include_router(actions_router)

    async def override_db():
        async with session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_db

    return app, runtime


async def test_action_executes_and_audits(session_factory) -> None:
    app, runtime = await _build_app(session_factory)

    try:
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/entities/fake_action.action-home.dev.switch/actions",
                json={
                    "action": "turn_on",
                    "capability": "on_off",
                    "params": {"level": 1},
                },
            )

            assert response.status_code == 200
            assert response.json() == {"ok": True, "message": "turned on"}

            audits = await client.get("/api/action-audits")

        assert audits.status_code == 200
        rows = audits.json()
        assert len(rows) == 1
        assert rows[0]["outcome"] == "ok"
        assert rows[0]["integration"] == "fake_action"

        async with session_factory() as db:
            stored = await ActionAuditRepository().list(db)

        assert len(stored) == 1
        assert stored[0].capability == "on_off"

    finally:
        await runtime.shutdown()


async def test_action_rejected_by_capability_is_audited(
    session_factory,
) -> None:
    app, runtime = await _build_app(session_factory)

    try:
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/entities/fake_action.action-home.dev.switch/actions",
                json={"action": "set_level", "capability": "set_level"},
            )

            assert response.status_code == 403

        async with session_factory() as db:
            stored = await ActionAuditRepository().list(db)

        # 集成 manifest 未声明 set_level，第一关就被拒绝
        assert len(stored) == 1
        assert stored[0].outcome == "rejected:manifest"

    finally:
        await runtime.shutdown()


async def test_action_entity_not_found(session_factory) -> None:
    app, runtime = await _build_app(session_factory)

    try:
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/entities/not.exists/actions",
                json={"action": "turn_on", "capability": "on_off"},
            )

        assert response.status_code == 404

    finally:
        await runtime.shutdown()
