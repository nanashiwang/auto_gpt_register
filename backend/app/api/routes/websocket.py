"""WebSocket 实时通信模块"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        """初始化连接管理器"""
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, task_id: str):
        """
        连接到任务

        Args:
            websocket: WebSocket 连接对象
            task_id: 任务 ID
        """
        await websocket.accept()

        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()

        self.active_connections[task_id].add(websocket)
        logger.info(f"WebSocket 连接建立: task_id={task_id}, "
                   f"当前连接数={len(self.active_connections[task_id])}")

    def disconnect(self, websocket: WebSocket, task_id: str):
        """
        断开连接

        Args:
            websocket: WebSocket 连接对象
            task_id: 任务 ID
        """
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)

            # 如果该任务没有连接了,删除任务条目
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]

        logger.info(f"WebSocket 连接断开: task_id={task_id}")

    async def broadcast(self, task_id: str, message: dict):
        """
        广播消息到任务的所有连接

        Args:
            task_id: 任务 ID
            message: 消息字典
        """
        if task_id not in self.active_connections:
            return

        disconnected = set()

        for connection in self.active_connections[task_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"发送消息失败: {str(e)}")
                disconnected.add(connection)

        # 清理断开的连接
        for connection in disconnected:
            self.disconnect(connection, task_id)

    async def send_progress(self, task_id: str, progress_data: dict):
        """
        发送进度更新

        Args:
            task_id: 任务 ID
            progress_data: 进度数据字典
        """
        message = {
            'type': 'progress',
            'data': progress_data
        }
        await self.broadcast(task_id, message)

    async def send_log(self, task_id: str, log_data: dict):
        """
        发送日志

        Args:
            task_id: 任务 ID
            log_data: 日志数据字典
        """
        message = {
            'type': 'log',
            'data': log_data
        }
        await self.broadcast(task_id, message)

    async def send_status(self, task_id: str, status_data: dict):
        """
        发送状态更新

        Args:
            task_id: 任务 ID
            status_data: 状态数据字典
        """
        message = {
            'type': 'status',
            'data': status_data
        }
        await self.broadcast(task_id, message)

    def get_connection_count(self, task_id: str) -> int:
        """
        获取指定任务的连接数

        Args:
            task_id: 任务 ID

        Returns:
            连接数量
        """
        return len(self.active_connections.get(task_id, set()))


# 全局连接管理器实例
manager = ConnectionManager()


@router.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """
    WebSocket 端点

    Args:
        websocket: WebSocket 连接对象
        task_id: 任务 ID
    """
    await manager.connect(websocket, task_id)

    try:
        # 发送连接成功消息
        await websocket.send_json({
            'type': 'connected',
            'task_id': task_id,
            'message': 'WebSocket 连接已建立'
        })

        # 保持连接并接收客户端消息
        while True:
            data = await websocket.receive_text()

            # 处理心跳
            if data == 'ping':
                await websocket.send_text('pong')
            elif data == 'ping_json':
                await websocket.send_json({'type': 'pong'})

    except WebSocketDisconnect:
        manager.disconnect(websocket, task_id)
        logger.info(f"WebSocket 正常断开: task_id={task_id}")
    except Exception as e:
        logger.error(f"WebSocket 错误: {str(e)}")
        manager.disconnect(websocket, task_id)
