import httpx

from app.core.config import settings


class AmapDistrictClient:

    BASE_URL = (
        "https://restapi.amap.com/v3/config/district"
    )

    async def query(
        self,
        keywords: str,
        subdistrict: int = 0,
        filter_adcode: str | None = None,
    ) -> list[dict]:

        params = {
            "key": settings.amap_web_service_key,
            "keywords": keywords,
            "subdistrict": subdistrict,
            "extensions": "base",
            "output": "JSON",
        }

        if filter_adcode:
            params["filter"] = filter_adcode

        async with httpx.AsyncClient(
            timeout=10
        ) as client:

            response = await client.get(
                self.BASE_URL,
                params=params,
            )

            response.raise_for_status()

            data = response.json()

        if data.get("status") != "1":
            raise RuntimeError(
                f"AMap district API failed: "
                f"{data.get('info')}"
            )

        return data.get("districts", [])