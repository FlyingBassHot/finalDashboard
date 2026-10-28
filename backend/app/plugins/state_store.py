"""运行期实体状态表（进程内存）。

数据库里的 ``entity_states`` 是持久化副本；轮询热路径优先读这里，
避免每次状态上报都回查 SQLite。重启时由持久化层回填。
"""

from collections.abc import Mapping

from app.domain.state import EntityState


class StateStore:
    def __init__(self) -> None:
        self._states: dict[str, EntityState] = {}

    def get(self, entity_id: str) -> EntityState | None:
        return self._states.get(entity_id)

    def set(self, entity_id: str, state: EntityState) -> None:
        self._states[entity_id] = state

    def all(self) -> Mapping[str, EntityState]:
        return dict(self._states)

    def load(self, states: Mapping[str, EntityState]) -> None:
        self._states.update(states)

    def remove(self, entity_id: str) -> None:
        self._states.pop(entity_id, None)

    def remove_by_prefix(self, prefix: str) -> None:
        for entity_id in [key for key in self._states if key.startswith(prefix)]:
            del self._states[entity_id]

    def clear(self) -> None:
        self._states.clear()
