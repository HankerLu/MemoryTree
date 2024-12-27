import asyncio
from typing import Any, Dict, Optional
from datetime import datetime
from copy import deepcopy
import logging

logger = logging.getLogger(__name__)


class MonitorPool:
    def __init__(self):
        self._data = {
            "workflows": {},  # 工作流相关数据
            "system": {},  # 系统级数据
            "chat": {}  # 对话相关数据
        }
        self._lock = asyncio.Lock()

    async def initialize(self):
        """初始化监控池"""
        try:
            current_time = datetime.now().isoformat()
            async with self._lock:
                # 只记录启动时间和状态
                self._data["system"]["start_time"] = {
                    "value": current_time,
                    "timestamp": current_time
                }
                self._data["system"]["status"] = {
                    "value": "running",
                    "timestamp": current_time
                }
                logger.info("监控池初始化完成")
        except Exception as e:
            logger.error(f"监控池初始化失败: {str(e)}")

    async def record(self, category: str, key: str, value: Any, unit_id: str = None, mode: str = "update"):
        """统一的记录接口"""
        try:
            async with self._lock:
                if unit_id:
                    # 工作流相关数据
                    if unit_id not in self._data["workflows"]:
                        self._data["workflows"][unit_id] = {}
                    target = self._data["workflows"][unit_id]
                else:
                    # 系统或对话数据
                    target = self._data[category]

                if mode == "append":
                    # 追加模式
                    if key not in target:
                        target[key] = []
                    target[key].append({
                        "value": value,
                        "timestamp": datetime.now().isoformat()
                    })
                elif mode == "merge":

                    # 合并模式（用于node_results）

                    if key not in target:
                        target[key] = {}

                    target[key].update(value)
                else:
                    # 更新模式
                    target[key] = {
                        "value": value,
                        "timestamp": datetime.now().isoformat()
                    }
                logger.debug(f"记录监控数据: category={category}, key={key}, unit_id={unit_id}")
        except Exception as e:
            logger.error(f"记录监控数据失败: {str(e)}")

    async def get_data(self, category: str = None, unit_id: str = None) -> Dict:
        """获取数据"""
        try:
            async with self._lock:
                if unit_id:
                    return deepcopy(self._data["workflows"].get(unit_id, {}))
                if category:
                    return deepcopy(self._data.get(category, {}))
                return deepcopy(self._data)
        except Exception as e:
            logger.error(f"获取监控数据失败: {str(e)}")
            return {}


# 创建全局实例
monitor_pool = MonitorPool()
