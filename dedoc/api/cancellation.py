import logging
from contextlib import asynccontextmanager

from anyio import create_task_group
from fastapi import Request


@asynccontextmanager
async def cancel_on_disconnect(request: Request, logger: logging.Logger) -> None:
    """
    Async context manager for async code that needs to be cancelled if client disconnects prematurely.
    The client disconnect is monitored through the Request object.

    Source: https://github.com/dorinclisu/runner-with-api
    See discussion: https://github.com/fastapi/fastapi/discussions/8805
    """
    async with create_task_group() as task_group:
        async def watch_disconnect() -> None:
            while True:
                message = await request.receive()

                if message["type"] == "http.disconnect":
                    client = f"{request.client.host}:{request.client.port}" if request.client else "-:-"
                    logger.warning(f"{client} - `{request.method} {request.url.path}` 499 DISCONNECTED")

                    task_group.cancel_scope.cancel()
                    break

        task_group.start_soon(watch_disconnect)

        try:
            yield
        finally:
            task_group.cancel_scope.cancel()
