"""Prometheus exporter 抓取集成包。"""

from app.integrations.prometheus_scrape.integration import (
    PrometheusScrapeIntegration,
)

__all__ = ["PrometheusScrapeIntegration"]
