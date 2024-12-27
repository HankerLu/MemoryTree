from typing import Dict, Optional, Any
from datetime import datetime
import uuid
import asyncio
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from .workflow_thread import WorkflowThread
import logging
from utils.monitor_pool import monitor_pool  # 添加导入

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
        self._lock = asyncio.Lock()  # 添加异步锁
        self._executor = ThreadPoolExecutor(max_workers=3)  # 创建线程池

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

        # 使用锁保护工作单元创建
        async with self._lock:
            self.work_units[unit_id] = work_unit

            # 添加监控点：更新系统工作流状态
            await monitor_pool.record(
                category="system",
                key="workflows_overview",
                value={
                    "all_workflows": list(self.work_units.keys()),
                    "active_workflows": [
                        wid for wid, unit in self.work_units.items()
                        if unit["status"] in ["pending", "processing"]
                    ],
                    "completed_workflows": [
                        wid for wid, unit in self.work_units.items()
                        if unit["status"] == "completed"
                    ],
                    "failed_workflows": [
                        wid for wid, unit in self.work_units.items()
                        if unit["status"] == "failed"
                    ]
                }
            )

        # 在新线程中启动工作流处理
        loop = asyncio.get_event_loop()
        loop.run_in_executor(self._executor, self._run_workflow, unit_id)

        return unit_id

    def _run_workflow(self, unit_id: str):
        """在独立线程中运行工作流"""
        try:
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # 获取该线程的数据库会话
            from database.mysql_connector import db_manager
            session = db_manager.get_session()

            try:
                # 运行工作流处理
                loop.run_until_complete(self._process_unit(unit_id))
            finally:
                # 清理数据库会话
                db_manager.close_session()

        except Exception as e:
            logger.error(f"工作流线程异常: {str(e)}")
        finally:
            loop.close()

    async def _process_unit(self, unit_id: str):
        """处理工作单元"""
        try:
            # 更新状态为处理中
            async with self._lock:
                work_unit = self.work_units[unit_id]
                work_unit["status"] = "processing"

                # 添加监控点：更新系统工作流状态
                await monitor_pool.record(
                    category="system",
                    key="workflows_overview",
                    value={
                        "all_workflows": list(self.work_units.keys()),
                        "active_workflows": [
                            wid for wid, unit in self.work_units.items()
                            if unit["status"] in ["pending", "processing"]
                        ],
                        "completed_workflows": [
                            wid for wid, unit in self.work_units.items()
                            if unit["status"] == "completed"
                        ],
                        "failed_workflows": [
                            wid for wid, unit in self.work_units.items()
                            if unit["status"] == "failed"
                        ]
                    }
                )

            # 处理工作单元
            result = await self.workflow_thread.process(
                work_unit,
                status_callback=self._update_status
            )

            # 更新处理结果
            async with self._lock:
                self.work_units[unit_id].update(result)

        except Exception as e:
            logger.error(f"工作单元处理失败: {str(e)}")
            async with self._lock:
                self.work_units[unit_id]["status"] = "failed"
                self.work_units[unit_id]["error"] = str(e)

                # 添加监控点：更新系统工作流状态
                await monitor_pool.record(
                    category="system",
                    key="workflows_overview",
                    value={
                        "all_workflows": list(self.work_units.keys()),
                        "active_workflows": [
                            wid for wid, unit in self.work_units.items()
                            if unit["status"] in ["pending", "processing"]
                        ],
                        "completed_workflows": [
                            wid for wid, unit in self.work_units.items()
                            if unit["status"] == "completed"
                        ],
                        "failed_workflows": [
                            wid for wid, unit in self.work_units.items()
                            if unit["status"] == "failed"
                        ]
                    }
                )

    async def _update_status(self, unit_id: str, status_update: Dict[str, Any]):
        """更新工作单元状态"""
        try:
            async with self._lock:
                if unit_id in self.work_units:
                    self.work_units[unit_id].update(status_update)
        except Exception as e:
            logger.error(f"状态更新失败: {str(e)}")

    async def get_unit_status(self, unit_id: str) -> Optional[Dict]:
        """获取工作单元状态"""
        try:
            async with self._lock:
                if unit_id not in self.work_units:
                    logger.error(f"工作单元不存在: {unit_id}")
                    return None

                # 创建深拷贝避免状态读取时的资源竞争
                unit = deepcopy(self.work_units[unit_id])

            # 验证状态数据完整性
            if not isinstance(unit, dict):
                logger.error(f"工作单元数据格式错误: {type(unit)}")
                return None

            required_fields = ["id", "type", "status", "create_time", "node_states"]
            if not all(field in unit for field in required_fields):
                logger.error(f"工作单元数据不完整: {unit.keys()}")
                return None

            logger.info(f"获取工作单元状态: {unit_id}, 当前状态: {unit['status']}")

            # 添加更多日志来调试
            logger.debug(f"工作单元完整数据: {unit}")

            return {
                "id": unit["id"],
                "type": unit["type"],
                "status": unit["status"],
                "create_time": unit["create_time"],
                "node_states": {
                    name: {k: datetime_to_str(v) for k, v in state.items()}
                    for name, state in unit["node_states"].items()
                },
                "error": unit.get("error"),
                "svg_ready": "svg" in unit.get("results", {})
            }

        except Exception as e:
            logger.error(f"获取工作单元状态异常: {str(e)}")
            return None

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

    def __del__(self):
        """清理资源"""
        self._executor.shutdown(wait=False)
