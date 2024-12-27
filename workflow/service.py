from typing import Dict, Any, Optional
from datetime import datetime
from .core.workflow_manager import WorkflowManager
import logging

logger = logging.getLogger(__name__)

class WorkflowService:
    """工作流服务：提供工作流相关的API接口"""
    
    def __init__(self):
        self.workflow_manager = WorkflowManager()
    
    async def create_workflow(self, data: Dict[str, Any], unit_type: str) -> str:
        """
        创建工作流
        Args:
            data: 初始数据
            unit_type: 工作单元类型 ("realtime" 或 "import")
        Returns:
            工作单元ID
        """
        return await self.workflow_manager.create_work_unit(data, unit_type)
    
    async def get_workflow_status(self, unit_id: str) -> Optional[Dict]:
        """获取工作流状态"""
        try:
            status = await self.workflow_manager.get_unit_status(unit_id)
            if not status:
                logger.warning(f"未找到工作单元: {unit_id}")
                return None
                
            logger.info(f"工作单元状态: {status['status']}, ID: {unit_id}")
            return status
            
        except Exception as e:
            logger.error(f"获取工作流状态失败: {str(e)}")
            raise
    
    async def get_svg_result(self, unit_id: str) -> Optional[Dict]:
        """
        获取SVG生成结果
        Args:
            unit_id: 工作单元ID
        Returns:
            SVG结果数据
        """
        return await self.workflow_manager.get_svg_result(unit_id)
    
    def cleanup(self, max_age_hours: int = 24):
        """
        清理旧的工作单元
        Args:
            max_age_hours: 最大保留时间（小时）
        """
        self.workflow_manager.cleanup_old_units(max_age_hours) 