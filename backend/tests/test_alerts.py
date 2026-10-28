"""Alertmanager webhook 落库与查询测试。"""

import pytest
from fastapi import HTTPException

from app.alerting.service import AlertService
from app.api.alerts import _verify_token
from app.core.config import settings
from app.schemas.alerts import AlertmanagerPayload


def _payload(
    *,
    status: str = "firing",
    fingerprint: str | None = "fp-1",
    summary: str = "device down",
) -> AlertmanagerPayload:
    return AlertmanagerPayload.model_validate(
        {
            "version": "4",
            "status": status,
            "receiver": "homehub",
            "groupKey": '{}:{alertname="DeviceDown"}',
            "externalURL": "http://alertmanager:9093",
            "alerts": [
                {
                    "status": status,
                    "labels": {
                        "alertname": "DeviceDown",
                        "severity": "critical",
                        "device_id": "openwrt.home.main",
                    },
                    "annotations": {
                        "summary": summary,
                        "description": "device is unreachable",
                    },
                    "startsAt": "2026-10-28T10:00:00Z",
                    "endsAt": "0001-01-01T00:00:00Z",
                    "generatorURL": "http://prometheus:9090/graph",
                    "fingerprint": fingerprint,
                },
            ],
        },
    )


async def test_alert_lifecycle(session_factory) -> None:
    service = AlertService()

    async with session_factory() as db:
        assert await service.ingest(db, _payload()) == 1

        alert = await service.get_alert(db, "fp-1")

        assert alert is not None
        assert alert.status == "firing"
        assert alert.name == "DeviceDown"
        assert alert.severity == "critical"
        assert alert.summary == "device down"
        assert alert.received_count == 1
        assert alert.ends_at is None  # 0001-01-01 归一为 None
        assert alert.resolved_at is None

        # 重复投递：更新而不是新增
        assert await service.ingest(db, _payload(summary="still down")) == 1

        alert = await service.get_alert(db, "fp-1")

        assert alert is not None
        assert alert.summary == "still down"
        assert alert.received_count == 2

        # resolved
        await service.ingest(db, _payload(status="resolved"))

        alert = await service.get_alert(db, "fp-1")

        assert alert is not None
        assert alert.status == "resolved"
        assert alert.resolved_at is not None

        # 再次 firing
        await service.ingest(db, _payload())

        alert = await service.get_alert(db, "fp-1")

        assert alert is not None
        assert alert.status == "firing"
        assert alert.resolved_at is None

        assert len(await service.list_alerts(db, status="firing")) == 1
        assert await service.list_alerts(db, status="resolved") == []


async def test_missing_fingerprint_is_derived(session_factory) -> None:
    service = AlertService()

    async with session_factory() as db:
        await service.ingest(db, _payload(fingerprint=None))

        alerts = await service.list_alerts(db)

        assert len(alerts) == 1
        assert len(alerts[0].fingerprint) == 64

        # 同样的 labels 第二次投递命中同一行
        await service.ingest(db, _payload(fingerprint=None))

        alerts = await service.list_alerts(db)

        assert len(alerts) == 1
        assert alerts[0].received_count == 2


def test_webhook_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "alert_webhook_token", "s3cret")

    _verify_token(None, "s3cret")
    _verify_token("Bearer s3cret", None)

    with pytest.raises(HTTPException) as exc_info:
        _verify_token("Bearer wrong", None)

    assert exc_info.value.status_code == 401

    with pytest.raises(HTTPException):
        _verify_token(None, None)
