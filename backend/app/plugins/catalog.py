"""内存设备 / 实体目录(规范化后的全局视图)。

当前为进程内实现;持久化接入后替换为 DB 支持的实现,
接口保持不变(与 history / repositories 的演进约定一致)。
"""

from app.domain.device import DeviceDescriptor
from app.domain.entity import EntityDescriptor


class EntityCatalog:
    """已注册设备与实物的全局目录。

    key 为规范化后的 device_id / entity_id
    (形如 "openwrt.main.wlan0_clients")。
    """

    def __init__(self) -> None:
        self._devices: dict[str, DeviceDescriptor] = {}
        self._entities: dict[str, EntityDescriptor] = {}

    def add_device(
        self,
        device: DeviceDescriptor,
    ) -> DeviceDescriptor:
        """注册 / 覆盖更新一个设备声明。"""

        self._devices[device.device_id] = device

        return device

    def add_entity(
        self,
        entity: EntityDescriptor,
    ) -> EntityDescriptor:
        """注册 / 覆盖更新一个实体声明。"""

        self._entities[entity.entity_id] = entity

        return entity

    def find_device(
        self,
        device_id: str,
    ) -> DeviceDescriptor | None:
        return self._devices.get(device_id)

    def find_entity(
        self,
        entity_id: str,
    ) -> EntityDescriptor | None:
        return self._entities.get(entity_id)

    def all_devices(self) -> list[DeviceDescriptor]:
        return list(self._devices.values())

    def all_entities(self) -> list[EntityDescriptor]:
        return list(self._entities.values())

    def remove_entity(self, entity_id: str) -> bool:
        return self._entities.pop(entity_id, None) is not None

    def remove_device(self, device_id: str) -> bool:
        return self._devices.pop(device_id, None) is not None

    def remove_by_prefix(self, prefix: str) -> None:
        for entity_id in [key for key in self._entities if key.startswith(prefix)]:
            del self._entities[entity_id]

        for device_id in [key for key in self._devices if key.startswith(prefix)]:
            del self._devices[device_id]

    def device_count(self) -> int:
        return len(self._devices)

    def entity_count(self) -> int:
        return len(self._entities)
