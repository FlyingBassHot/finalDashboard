"""Alertmanager 报文归一化。"""

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime

from app.schemas.alerts import AlertmanagerAlert


@dataclass(frozen=True, slots=True)
class NormalizedAlert:
    fingerprint: str
    name: str
    status: str
    severity: str
    summary: str | None
    description: str | None
    labels: dict[str, str]
    annotations: dict[str, str]
    starts_at: datetime | None
    ends_at: datetime | None
    generator_url: str | None


def _parse_time(value: datetime | None) -> datetime | None:
    if value is None:
        return None

    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)

    # Alertmanager 对未结束的告警使用 0001-01-01T00:00:00Z
    if value.year <= 1:
        return None

    return value.astimezone(UTC)


def _fingerprint(alert: AlertmanagerAlert) -> str:
    if alert.fingerprint and alert.fingerprint.strip():
        return alert.fingerprint.strip()[:64]

    raw = json.dumps(
        alert.labels,
        sort_keys=True,
        ensure_ascii=False,
    )

    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:64]


def normalize_alert(alert: AlertmanagerAlert) -> NormalizedAlert:
    labels = dict(alert.labels)
    annotations = dict(alert.annotations)

    return NormalizedAlert(
        fingerprint=_fingerprint(alert),
        name=labels.get("alertname") or "unknown",
        status=alert.status,
        severity=labels.get("severity") or "",
        summary=annotations.get("summary"),
        description=annotations.get("description"),
        labels=labels,
        annotations=annotations,
        starts_at=_parse_time(alert.startsAt),
        ends_at=_parse_time(alert.endsAt),
        generator_url=alert.generatorURL,
    )
