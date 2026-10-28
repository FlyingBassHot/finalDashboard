"""拓扑数据对象 —— 集成上报的网络邻居信息。"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Neighbor:
    """一条邻居记录(来自 ARP / 无线客户端表 / FDB 等)。"""

    mac: str
    """MAC 地址(必填,设备绑定的主键)。"""

    ip: str | None = None
    hostname: str | None = None
    interface: str | None = None
    """所在接口,如 "br-lan"、"wlan0"。"""

    source: str = "arp"
    """数据来源:"arp" / "iwinfo" / "fdb" 等。"""

    is_wireless: bool = False
    """是否无线客户端。"""
