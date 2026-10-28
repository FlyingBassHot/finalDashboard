import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class AmapConfigError(RuntimeError):
    """高德服务未配置（缺少 Key）。"""


class AmapDistrictClient:
    BASE_URL = "https://restapi.amap.com/v3/config/district"

    async def query(
        self,
        keywords: str,
        subdistrict: int = 0,
        filter_adcode: str | None = None,
    ) -> list[dict]:
        if not settings.amap_web_service_key:
            raise AmapConfigError(
                "AMAP_WEB_SERVICE_KEY 未配置，无法使用行政区搜索",
            )

        params = {
            "key": settings.amap_web_service_key,
            "keywords": keywords,
            "subdistrict": subdistrict,
            "extensions": "base",
            "output": "JSON",
        }

        if filter_adcode:
            params["filter"] = filter_adcode

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()

        except httpx.HTTPError:
            logger.warning(
                "AMap district request failed: keywords=%r subdistrict=%s",
                keywords,
                subdistrict,
                exc_info=True,
            )
            raise

        if data.get("status") != "1":
            raise RuntimeError(
                f"AMap district API failed: {data.get('info')}",
            )

        return data.get("districts", [])
