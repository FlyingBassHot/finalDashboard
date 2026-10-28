"""集成 API 出参的脱敏测试。"""

from datetime import UTC, datetime

from app.schemas.integrations import IntegrationInstanceResponse


def test_instance_response_redacts_secrets() -> None:
    now = datetime.now(UTC)

    response = IntegrationInstanceResponse(
        id=1,
        name="openwrt-main",
        integration="openwrt",
        display_name="OpenWrt",
        config={
            "host": "192.168.1.1",
            "password": "plain-text",
            "nested": {"token": "abc", "port": 80},
        },
        poll_interval_seconds=60,
        enabled=True,
        last_started_at=None,
        last_poll_at=None,
        last_success_at=None,
        last_error=None,
        created_at=now,
        updated_at=now,
    )

    assert response.model_dump()["config"] == {
        "host": "192.168.1.1",
        "password": "***",
        "nested": {"token": "***", "port": 80},
    }
