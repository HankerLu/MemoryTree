from typing import Dict, Optional, Any
from datetime import datetime
import uuid
import asyncio
from .workflow_thread import WorkflowThread
import logging

logger = logging.getLogger(__name__)


def datetime_to_str(obj: Any) -> Any:
    """转换datetime对象为ISO格式字符串"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj


class WorkflowManager:
    """工作流管理器：负责工作单元的创建和管理"""

    def __init__(self):
        self.work_units = {}  # 存储所有工作单元
        self.workflow_thread = WorkflowThread()

    async def create_work_unit(self, data: Dict[str, Any], unit_type: str) -> str:
        """创建新的工作单元"""
        unit_id = str(uuid.uuid4())
        work_unit = {
            "id": unit_id,
            "type": unit_type,
            "status": "pending",
            "create_time": datetime.now().isoformat(),
            "data": data,
            "results": {},
            "node_states": {},
            "error": None
        }

        self.work_units[unit_id] = work_unit

        # 在新的事件循环中处理工作单元
        asyncio.create_task(self._process_unit(unit_id))
        return unit_id

    async def get_unit_status(self, unit_id: str) -> Optional[Dict]:
        """获取工作单元状态"""

        if unit_id not in self.work_units:
            return None

        unit = self.work_units[unit_id]

        return {
            "id": unit["id"],
            "type": unit["type"],
            "status": unit["status"],
            "create_time": unit["create_time"],
            "node_states": {
                name: {k: datetime_to_str(v) for k, v in state.items()}
                for name, state in unit["node_states"].items()
            },
            "error": unit["error"],
            "svg_ready": "svg" in unit["results"]
        }

    async def get_svg_result(self, unit_id: str) -> Optional[Dict]:
        """获取SVG生成结果"""
        try:
            if unit_id not in self.work_units:
                return None

            unit = self.work_units[unit_id]
            if "svg" not in unit["results"]:
                return None

            svg_data = unit["results"].get("svg", {})

            # 检查必要字段
            if not all(k in svg_data for k in ["content", "type", "metadata"]):
                logger.error(f"SVG数据格式错误: {svg_data.keys()}")
                return None

            if not svg_data["content"]:  # 检查内容是否为空
                logger.error("SVG内容为空")
                return None

            # 转换为符合 SVGResult 模型的格式
            return {
                "content": svg_data["content"][0],  # 取第一页SVG内容
                "type": svg_data["type"],
                "metadata": svg_data["metadata"]
            }
        except Exception as e:
            logger.error(f"获取SVG结果出错: {str(e)}")
            return None

    async def _process_unit(self, unit_id: str):
        """处理工作单元"""
        work_unit = self.work_units[unit_id]

        try:
            work_unit["status"] = "processing"
            result = await self.workflow_thread.process(work_unit)

        except Exception as e:
            work_unit["status"] = "failed"
            work_unit["error"] = str(e)

    def cleanup_old_units(self, max_age_hours: int = 24):
        """清理旧的工作单元"""
        now = datetime.now()
        to_delete = []

        for unit_id, unit in self.work_units.items():
            create_time = datetime.fromisoformat(unit["create_time"])
            age = now - create_time
            if age.total_seconds() > max_age_hours * 3600:
                to_delete.append(unit_id)

        for unit_id in to_delete:
            del self.work_units[unit_id]
