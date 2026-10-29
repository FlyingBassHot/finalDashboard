"""exporter 原始指标 → 统一实体读数。

只依赖 node_exporter 的标准指标名；缺少某个指标时跳过对应实体，
不会让整次采集失败。实体 key 与 OpenWrt 集成保持一致，前端可复用同一套卡片。
"""

import math
from dataclasses import dataclass
from typing import Any

from prometheus_client.parser import text_string_to_metric_families
from prometheus_client.samples import Sample

from app.plugins.errors import IntegrationError

MIB = 1024 * 1024


@dataclass(frozen=True, slots=True)
class Reading:
    key: str
    name: str
    value: Any
    domain: str = "sensor"
    unit: str | None = None


def parse_exposition(text: str) -> dict[str, list[Sample]]:
    """解析 Prometheus 文本格式，按样本名建立索引。"""

    index: dict[str, list[Sample]] = {}

    try:
        for family in text_string_to_metric_families(text):
            for sample in family.samples:
                index.setdefault(sample.name, []).append(sample)

    except ValueError as exc:
        raise IntegrationError(f"invalid exposition format: {exc}") from exc

    return index


def _first_value(
    index: dict[str, list[Sample]],
    name: str,
    **labels: str,
) -> float | None:
    for sample in index.get(name, []):
        if any(sample.labels.get(key) != value for key, value in labels.items()):
            continue

        value = float(sample.value)

        if math.isnan(value):
            return None

        return value

    return None


def _first_labels(index: dict[str, list[Sample]], name: str) -> dict[str, str] | None:
    samples = index.get(name)

    return dict(samples[0].labels) if samples else None


def build_readings(
    index: dict[str, list[Sample]],
    *,
    disk_mountpoint: str = "/",
) -> list[Reading]:
    readings: list[Reading] = []

    load_1m = _first_value(index, "node_load1")

    if load_1m is not None:
        readings.append(
            Reading("load_1m", "1 分钟负载", round(load_1m, 2)),
        )

    now = _first_value(index, "node_time_seconds")
    boot = _first_value(index, "node_boot_time_seconds")

    if now is not None and boot is not None and now >= boot:
        readings.append(
            Reading("uptime", "运行时长", int(now - boot), unit="s"),
        )

    memory_total = _first_value(index, "node_memory_MemTotal_bytes")
    memory_available = _first_value(index, "node_memory_MemAvailable_bytes")

    if memory_total and memory_total > 0 and memory_available is not None:
        used = max(0.0, memory_total - memory_available)

        readings.extend(
            [
                Reading(
                    "memory_total",
                    "内存总量",
                    round(memory_total / MIB, 1),
                    unit="MB",
                ),
                Reading(
                    "memory_used",
                    "内存占用",
                    round(used / MIB, 1),
                    unit="MB",
                ),
                Reading(
                    "memory_usage",
                    "内存使用率",
                    round(used / memory_total * 100, 1),
                    unit="%",
                ),
            ],
        )

    disk_size = _first_value(
        index,
        "node_filesystem_size_bytes",
        mountpoint=disk_mountpoint,
    )
    disk_available = _first_value(
        index,
        "node_filesystem_avail_bytes",
        mountpoint=disk_mountpoint,
    )

    if disk_size and disk_size > 0 and disk_available is not None:
        used = max(0.0, disk_size - disk_available)

        readings.extend(
            [
                Reading(
                    "disk_total",
                    "磁盘总量",
                    round(disk_size / MIB, 1),
                    unit="MB",
                ),
                Reading(
                    "disk_usage",
                    "磁盘使用率",
                    round(used / disk_size * 100, 1),
                    unit="%",
                ),
            ],
        )

    os_labels = _first_labels(index, "node_os_info")

    if os_labels:
        os_name = os_labels.get("name", "")
        os_version = os_labels.get("version", "")
        text = " ".join(part for part in [os_name, os_version] if part)

        if text:
            readings.append(Reading("os_version", "系统版本", text))

    return readings
