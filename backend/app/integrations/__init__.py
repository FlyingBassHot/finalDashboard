"""南向集成包。

导入本包即完成内置集成向默认注册表的注册。
"""

from app.integrations.openwrt.integration import OpenWrtIntegration
from app.integrations.prometheus_scrape.integration import (
    PrometheusScrapeIntegration,
)

__all__ = ["OpenWrtIntegration", "PrometheusScrapeIntegration"]
