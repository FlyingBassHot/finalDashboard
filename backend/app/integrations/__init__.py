"""南向集成包。

导入本包即完成内置集成向默认注册表的注册。
"""

from app.integrations.openwrt.integration import OpenWrtIntegration

__all__ = ["OpenWrtIntegration"]
