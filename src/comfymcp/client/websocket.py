"""WebSocket client for ComfyUI real-time events."""

import asyncio
import json
import logging
import uuid
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any

import aiohttp

from comfymcp.client.types import (
    ExecutionEvent,
    ExecutionEventType,
    ProgressEvent,
)

logger = logging.getLogger(__name__)


class ComfyUIWebSocket:
    """WebSocket client for ComfyUI real-time event streaming."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8188,
        client_id: str | None = None,
        reconnect_interval: float = 5.0,
        max_reconnect_attempts: int = 10,
    ):
        self.host = host
        self.port = port
        self.client_id = client_id or str(uuid.uuid4())
        self.reconnect_interval = reconnect_interval
        self.max_reconnect_attempts = max_reconnect_attempts

        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._session: aiohttp.ClientSession | None = None
        self._connected = False
        self._reconnect_task: asyncio.Task | None = None

        # Event handlers
        self._event_handlers: dict[ExecutionEventType, list[Callable]] = {
            event_type: [] for event_type in ExecutionEventType
        }
        self._global_handlers: list[Callable] = []
        self._prompt_handlers: dict[str, list[Callable]] = {}

    @property
    def ws_url(self) -> str:
        """Get the WebSocket URL."""
        return f"ws://{self.host}:{self.port}/ws?clientId={self.client_id}"

    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self._connected and self._ws is not None and not self._ws.closed

    async def connect(self) -> None:
        """Connect to the ComfyUI WebSocket."""
        if self.is_connected:
            return

        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()

        try:
            self._ws = await self._session.ws_connect(self.ws_url)
            self._connected = True
            logger.info(f"Connected to ComfyUI WebSocket: {self.ws_url}")
        except aiohttp.ClientError as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from the WebSocket."""
        self._connected = False

        if self._reconnect_task:
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass
            self._reconnect_task = None

        if self._ws and not self._ws.closed:
            await self._ws.close()
            self._ws = None

        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

        logger.info("Disconnected from ComfyUI WebSocket")

    async def __aenter__(self) -> "ComfyUIWebSocket":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    def on_event(
        self,
        event_type: ExecutionEventType | None = None,
        prompt_id: str | None = None,
    ) -> Callable:
        """Decorator to register an event handler.

        Args:
            event_type: Specific event type to handle, or None for all events
            prompt_id: Specific prompt to handle events for, or None for all

        Example:
            @ws.on_event(ExecutionEventType.PROGRESS)
            async def handle_progress(event: ExecutionEvent):
                print(f"Progress: {event.data}")
        """
        def decorator(func: Callable) -> Callable:
            if prompt_id:
                if prompt_id not in self._prompt_handlers:
                    self._prompt_handlers[prompt_id] = []
                self._prompt_handlers[prompt_id].append((event_type, func))
            elif event_type:
                self._event_handlers[event_type].append(func)
            else:
                self._global_handlers.append(func)
            return func
        return decorator

    def add_handler(
        self,
        handler: Callable,
        event_type: ExecutionEventType | None = None,
        prompt_id: str | None = None,
    ) -> None:
        """Add an event handler programmatically."""
        if prompt_id:
            if prompt_id not in self._prompt_handlers:
                self._prompt_handlers[prompt_id] = []
            self._prompt_handlers[prompt_id].append((event_type, handler))
        elif event_type:
            self._event_handlers[event_type].append(handler)
        else:
            self._global_handlers.append(handler)

    def remove_handler(
        self,
        handler: Callable,
        event_type: ExecutionEventType | None = None,
        prompt_id: str | None = None,
    ) -> None:
        """Remove an event handler."""
        if prompt_id and prompt_id in self._prompt_handlers:
            self._prompt_handlers[prompt_id] = [
                (et, h) for et, h in self._prompt_handlers[prompt_id]
                if h != handler
            ]
        elif event_type:
            if handler in self._event_handlers[event_type]:
                self._event_handlers[event_type].remove(handler)
        else:
            if handler in self._global_handlers:
                self._global_handlers.remove(handler)

    def clear_prompt_handlers(self, prompt_id: str) -> None:
        """Clear all handlers for a specific prompt."""
        if prompt_id in self._prompt_handlers:
            del self._prompt_handlers[prompt_id]

    async def _dispatch_event(self, event: ExecutionEvent) -> None:
        """Dispatch an event to registered handlers."""
        handlers_to_call = []

        # Global handlers
        handlers_to_call.extend(self._global_handlers)

        # Type-specific handlers
        handlers_to_call.extend(self._event_handlers[event.type])

        # Prompt-specific handlers
        if event.prompt_id and event.prompt_id in self._prompt_handlers:
            for event_type, handler in self._prompt_handlers[event.prompt_id]:
                if event_type is None or event_type == event.type:
                    handlers_to_call.append(handler)

        # Call all handlers
        for handler in handlers_to_call:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Error in event handler: {e}")

    async def listen(self) -> AsyncIterator[ExecutionEvent]:
        """Listen for WebSocket events.

        Yields:
            ExecutionEvent objects as they arrive

        Example:
            async for event in ws.listen():
                print(f"Event: {event.type}")
        """
        if not self.is_connected:
            await self.connect()

        assert self._ws is not None

        reconnect_attempts = 0

        while True:
            try:
                msg = await self._ws.receive()

                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    event = ExecutionEvent.from_message(data)
                    await self._dispatch_event(event)
                    yield event
                    reconnect_attempts = 0

                elif msg.type == aiohttp.WSMsgType.BINARY:
                    # Binary data is preview images, skip for now
                    # Could be extended to handle previews
                    continue

                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    logger.warning("WebSocket closed by server")
                    if reconnect_attempts < self.max_reconnect_attempts:
                        reconnect_attempts += 1
                        await self._reconnect()
                    else:
                        logger.error("Max reconnection attempts reached")
                        break

                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {self._ws.exception()}")
                    break

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error receiving WebSocket message: {e}")
                if reconnect_attempts < self.max_reconnect_attempts:
                    reconnect_attempts += 1
                    await self._reconnect()
                else:
                    break

    async def _reconnect(self) -> None:
        """Attempt to reconnect to the WebSocket."""
        logger.info(f"Attempting to reconnect in {self.reconnect_interval}s...")
        await asyncio.sleep(self.reconnect_interval)

        try:
            if self._ws and not self._ws.closed:
                await self._ws.close()
            await self.connect()
            logger.info("Reconnected to WebSocket")
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
            raise

    async def wait_for_completion(
        self,
        prompt_id: str,
        timeout: float | None = None,
    ) -> ExecutionEvent:
        """Wait for a prompt to complete execution.

        Args:
            prompt_id: The prompt ID to wait for
            timeout: Maximum time to wait in seconds

        Returns:
            The final execution event (success, error, or interrupted)

        Raises:
            asyncio.TimeoutError: If timeout is reached
        """
        completion_events = {
            ExecutionEventType.EXECUTION_SUCCESS,
            ExecutionEventType.EXECUTION_ERROR,
            ExecutionEventType.EXECUTION_INTERRUPTED,
        }

        async def _wait():
            async for event in self.listen():
                if event.prompt_id == prompt_id and event.type in completion_events:
                    return event

        if timeout:
            return await asyncio.wait_for(_wait(), timeout=timeout)
        return await _wait()

    @asynccontextmanager
    async def track_execution(
        self,
        prompt_id: str,
        on_progress: Callable[[ProgressEvent], Any] | None = None,
        on_node_start: Callable[[str], Any] | None = None,
        on_node_complete: Callable[[str, dict], Any] | None = None,
    ) -> AsyncIterator["ExecutionTracker"]:
        """Context manager to track execution of a specific prompt.

        Args:
            prompt_id: The prompt ID to track
            on_progress: Callback for progress updates
            on_node_start: Callback when a node starts (receives node_id)
            on_node_complete: Callback when a node completes (receives node_id, output)

        Example:
            async with ws.track_execution(prompt_id, on_progress=print_progress):
                # Wait for completion
                pass
        """
        tracker = ExecutionTracker(
            ws=self,
            prompt_id=prompt_id,
            on_progress=on_progress,
            on_node_start=on_node_start,
            on_node_complete=on_node_complete,
        )
        await tracker.start()
        try:
            yield tracker
        finally:
            await tracker.stop()


class ExecutionTracker:
    """Tracks the execution of a specific prompt."""

    def __init__(
        self,
        ws: ComfyUIWebSocket,
        prompt_id: str,
        on_progress: Callable[[ProgressEvent], Any] | None = None,
        on_node_start: Callable[[str], Any] | None = None,
        on_node_complete: Callable[[str, dict], Any] | None = None,
    ):
        self.ws = ws
        self.prompt_id = prompt_id
        self.on_progress = on_progress
        self.on_node_start = on_node_start
        self.on_node_complete = on_node_complete

        self.started = False
        self.completed = False
        self.success = False
        self.error: dict | None = None
        self.outputs: dict[str, Any] = {}
        self.current_node: str | None = None

        self._listen_task: asyncio.Task | None = None
        self._completion_event = asyncio.Event()

    async def start(self) -> None:
        """Start tracking execution."""
        self._listen_task = asyncio.create_task(self._listen())

    async def stop(self) -> None:
        """Stop tracking execution."""
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass

    async def wait(self, timeout: float | None = None) -> bool:
        """Wait for execution to complete.

        Returns:
            True if successful, False otherwise
        """
        if timeout:
            await asyncio.wait_for(self._completion_event.wait(), timeout)
        else:
            await self._completion_event.wait()
        return self.success

    async def _listen(self) -> None:
        """Listen for events related to this prompt."""
        async for event in self.ws.listen():
            if event.prompt_id != self.prompt_id:
                continue

            if event.type == ExecutionEventType.EXECUTION_START:
                self.started = True

            elif event.type == ExecutionEventType.EXECUTING:
                node_id = event.data.get("node")
                if node_id is None:
                    # Execution complete
                    continue
                self.current_node = node_id
                if self.on_node_start:
                    result = self.on_node_start(node_id)
                    if asyncio.iscoroutine(result):
                        await result

            elif event.type == ExecutionEventType.EXECUTED:
                node_id = event.data.get("node")
                output = event.data.get("output", {})
                if node_id:
                    self.outputs[node_id] = output
                    if self.on_node_complete:
                        result = self.on_node_complete(node_id, output)
                        if asyncio.iscoroutine(result):
                            await result

            elif event.type == ExecutionEventType.PROGRESS:
                if self.on_progress:
                    progress = ProgressEvent.from_data(event.data)
                    result = self.on_progress(progress)
                    if asyncio.iscoroutine(result):
                        await result

            elif event.type == ExecutionEventType.EXECUTION_SUCCESS:
                self.completed = True
                self.success = True
                self._completion_event.set()
                break

            elif event.type in (
                ExecutionEventType.EXECUTION_ERROR,
                ExecutionEventType.EXECUTION_INTERRUPTED,
            ):
                self.completed = True
                self.success = False
                self.error = event.data
                self._completion_event.set()
                break
