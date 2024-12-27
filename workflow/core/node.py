from typing import Dict, Any
from datetime import datetime
from enum import Enum


class NodeStatus(Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class BaseNode:
    """节点基类，定义了节点的基本接口和状态管理"""

    def __init__(self, name: str):
        self.name = name
        self.status = NodeStatus.IDLE

    async def process(self, work_unit: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理工作单元数据
        Args:
            work_unit: 工作单元数据
        Returns:
            处理后的工作单元数据
        """
        try:
            self.status = NodeStatus.PROCESSING

            # 记录节点开始处理
            work_unit["node_states"][self.name] = {
                "status": self.status.value,
                "start_time": datetime.now()
            }

            # 执行具体处理逻辑，传入整个work_unit
            result = await self._process(work_unit)

            # 更新处理结果和状态
            self.status = NodeStatus.COMPLETED
            if "results" not in work_unit:
                work_unit["results"] = {}
            work_unit["results"][self.name] = result
            work_unit["node_states"][self.name].update({
                "status": self.status.value,
                "end_time": datetime.now()
            })

            return work_unit

        except Exception as e:
            self.status = NodeStatus.ERROR
            work_unit["node_states"][self.name].update({
                "status": self.status.value,
                "error": str(e),
                "end_time": datetime.now()
            })
            raise

    async def _process(self, work_unit: Dict[str, Any]) -> Dict[str, Any]:
        """具体节点需要实现的处理逻辑"""
        raise NotImplementedError

    def get_status(self) -> Dict[str, Any]:
        """获取节点当前状态"""
        return {
            "name": self.name,
            "status": self.status.value
        }
