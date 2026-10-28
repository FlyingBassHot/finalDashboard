"""ORM 模型统一出口。

``app.models`` 被导入时即完成所有模型的注册，``Base.metadata`` 才是完整的。
调用方只需 ``import app.models``，不必逐个导入。
"""

from app.models.alert import Alert
from app.models.device import Device
from app.models.entity import Entity
from app.models.entity_history import EntityHistory
from app.models.entity_state import EntityStateRecord
from app.models.home_settings import HomeSettings
from app.models.integration_instance import IntegrationInstance
from app.models.neighbor_link import NeighborLink
from app.models.weather_current import WeatherCurrent
from app.models.weather_daily import WeatherDaily

__all__ = [
    "Alert",
    "Device",
    "Entity",
    "EntityHistory",
    "EntityStateRecord",
    "HomeSettings",
    "IntegrationInstance",
    "NeighborLink",
    "WeatherCurrent",
    "WeatherDaily",
]
