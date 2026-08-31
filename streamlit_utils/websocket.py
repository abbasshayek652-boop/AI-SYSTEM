"""WebSocket utilities for real-time updates"""
import asyncio
import json
import logging
from typing import Any, Callable, Optional
from datetime import datetime

import httpx
from streamlit import session_state as st_session

logger = logging.getLogger(__name__)


class StreamlitWebSocketClient:
    """WebSocket client for real-time dashboard updates"""
    
    def __init__(self, base_url: str, token: Optional[str] = None):
        self.base_url = base_url.replace("http", "ws")
        self.token = token
        self.websocket = None
        self.connected = False
        self._callbacks: dict[str, list[Callable]] = {}
    
    async def connect(self) -> bool:
        """Connect to WebSocket server"""
        try:
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            
            # Note: WebSocket connection would be implemented here
            # This is a placeholder for future enhancement
            self.connected = True
            logger.info("WebSocket connected")
            return True
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from WebSocket server"""
        if self.websocket:
            await self.websocket.close()
        self.connected = False
        logger.info("WebSocket disconnected")
    
    def on(self, event: str, callback: Callable) -> None:
        """Register callback for event"""
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)
    
    async def emit(self, event: str, data: Any) -> None:
        """Emit event to server"""
        try:
            message = {
                "event": event,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            if self.websocket:
                await self.websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to emit event: {e}")
    
    async def listen(self) -> None:
        """Listen for incoming messages"""
        if not self.websocket:
            return
        
        try:
            async for message in self.websocket.iter_json():
                event = message.get("event")
                data = message.get("data")
                
                if event in self._callbacks:
                    for callback in self._callbacks[event]:
                        await callback(data) if asyncio.iscoroutinefunction(callback) else callback(data)
        except Exception as e:
            logger.error(f"WebSocket listening error: {e}")
            self.connected = False


async def fetch_agent_status_stream(
    base_url: str,
    agent_key: str,
    token: str,
    interval: float = 5.0
) -> None:
    """Stream agent status updates"""
    while True:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{base_url}/agents/{agent_key}/status",
                    headers={"Authorization": f"Bearer {token}"}
                )
                if response.status_code == 200:
                    data = response.json()
                    yield data
        except Exception as e:
            logger.error(f"Status stream error: {e}")
        
        await asyncio.sleep(interval)


async def fetch_market_data_stream(
    base_url: str,
    symbol: str,
    token: str,
    interval: float = 2.0
) -> None:
    """Stream market ticker updates"""
    while True:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{base_url}/exchange/ticker/{symbol}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                if response.status_code == 200:
                    data = response.json()
                    yield data
        except Exception as e:
            logger.error(f"Market stream error: {e}")
        
        await asyncio.sleep(interval)
