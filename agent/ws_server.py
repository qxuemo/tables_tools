"""WebSocket 推送服务 — 向连接的前端广播扫描进度."""
import asyncio
import json
import logging
from typing import Any, Optional

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
except ImportError:
    websockets = None
    WebSocketServerProtocol = None  # type: ignore

logger = logging.getLogger(__name__)


class ProgressServer:
    def __init__(self, port: int = 8765):
        self.port = port
        self._clients: list = []
        self._server = None
        self._running = False

    async def start(self) -> None:
        if websockets is None:
            raise ImportError(
                "websockets is not installed. Run: pip install websockets"
            )
        self._server = await websockets.serve(
            self._handler, "localhost", self.port
        )
        self._running = True
        logger.info(f"WS server started on ws://localhost:{self.port}")

    async def _handler(self, websocket: WebSocketServerProtocol) -> None:
        self._clients.append(websocket)
        try:
            async for _ in websocket:
                pass  # 忽略客户端消息
        finally:
            self._clients.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        data = json.dumps(message)
        dead: list = []
        for ws in self._clients:
            try:
                await ws.send(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._clients.remove(ws)

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._running = False

    def send_sync(self, message: Dict[str, Any]) -> None:
        """同步包装，供非 async 代码调用."""
        if not self._running:
            return
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.broadcast(message))
            else:
                loop.run_until_complete(self.broadcast(message))
        except Exception:
            pass
