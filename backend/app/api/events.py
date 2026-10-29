"""实时事件流（SSE）。

传输层实现细节；事件结构由 app.realtime.serializers 定义。
"""

import asyncio
import json

from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse

from app.api.deps import get_runtime

router = APIRouter(tags=["Realtime"])

HEARTBEAT_SECONDS = 15


@router.get("/api/events", summary="Realtime event stream (SSE)")
async def stream_events(
    request: Request,
    types: str | None = Query(
        default=None,
        description="逗号分隔的事件类型，如 state_changed,device_availability",
    ),
):
    runtime = get_runtime(request)

    selected = None

    if types:
        selected = frozenset(item.strip() for item in types.split(",") if item.strip())

    subscription = runtime.realtime.subscribe(selected)

    async def event_stream():
        try:
            yield ": connected\n\n"

            while True:
                if await request.is_disconnected():
                    break

                try:
                    payload = await asyncio.wait_for(
                        subscription.queue.get(),
                        timeout=HEARTBEAT_SECONDS,
                    )

                except TimeoutError:
                    yield ": ping\n\n"
                    continue

                data = json.dumps(
                    payload,
                    ensure_ascii=False,
                    default=str,
                )

                yield (f"event: {payload['type']}\ndata: {data}\n\n")

        finally:
            runtime.realtime.unsubscribe(subscription)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
