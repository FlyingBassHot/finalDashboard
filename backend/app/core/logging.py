"""应用日志初始化。

只配置 ``app`` 命名空间，避免覆盖 uvicorn / 第三方库的日志设置。
"""

import logging


def configure_logging(level: int = logging.INFO) -> None:
    logger = logging.getLogger("app")

    if logger.handlers:
        logger.setLevel(level)
        return

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        ),
    )

    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
