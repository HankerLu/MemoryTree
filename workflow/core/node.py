from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
import asyncio

class NodeStatus(Enum):
    WAITING = "waiting"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"

class Node:
    """工作流节点基类"""
    def __init__(self, node_id: str, node_name: str):
        self.node_id = node_id
        self.node_name = node_name
        self.status = NodeStatus.WAITING
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.input_data: Dict[str, Any] = {}
        self.output_data: Dict[str, Any] = {}
        self.error_info: str = ""
        self._process_func = None  # 节点的处理函数

    def set_process_func(self, func):
        """设置节点的处理函数"""
        self._process_func = func

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理节点任务"""
        try:
            self.status = NodeStatus.RUNNING
            self.start_time = datetime.now()
            self.input_data = input_data

            if self._process_func:
                # 确保处理函数是异步的
                if asyncio.iscoroutinefunction(self._process_func):
                    self.output_data = await self._process_func(input_data)
                else:
                    self.output_data = self._process_func(input_data)

                self.status = NodeStatus.COMPLETED
            else:
                raise ValueError(f"节点 {self.node_id} 未设置处理函数")

        except Exception as e:
            self.status = NodeStatus.ERROR
            self.error_info = str(e)
            raise
        finally:
            self.end_time = datetime.now()

        return self.output_data

    def reset(self):
        """重置节点状态"""
        self.status = NodeStatus.WAITING
        self.start_time = None
        self.end_time = None
        self.input_data = {}
        self.output_data = {}
        self.error_info = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "node_id": self.node_id,
            "node_name": self.node_name,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "error_info": self.error_info
        } 