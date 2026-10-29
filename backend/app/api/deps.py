"""FastAPI 依赖：运行期对象。"""

from fastapi import HTTPException, Request

from app.plugins.runtime import Runtime


def get_runtime(request: Request) -> Runtime:
    runtime = getattr(request.app.state, "runtime", None)

    if not isinstance(runtime, Runtime):
        raise HTTPException(
            status_code=503,
            detail="Runtime is not ready",
        )

    return runtime
