from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from .node import Node, NodeStatus
import logging
import asyncio
from PyQt5.QtCore import QTimer

logger = logging.getLogger(__name__)

class WorkflowManager:
    """工作流管理器，负责协调和监控整个工作流程"""
    
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.node_sequence: List[str] = []
        self.current_node_index: int = -1
        self.current_node: Optional[str] = None
        self.previous_node: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self._status_callback: Optional[Callable] = None

    def set_status_callback(self, callback: Callable):
        """设置状态更新回调函数，用于通知UI更新"""
        self._status_callback = callback

    def add_node(self, node_id: str, node_name: str, process_func) -> None:
        """添加节点到工作流"""
        if node_id in self.nodes:
            raise ValueError(f"节点 {node_id} 已存在")
            
        node = Node(node_id, node_name)
        node.set_process_func(process_func)
        self.nodes[node_id] = node
        self.node_sequence.append(node_id)

    async def execute_workflow(self, initial_input: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流"""
        try:
            logger.info("开始执行工作流")
            logger.info(f"初始输入: {initial_input}")
            
            # 重置工作流状态
            self.reset_workflow()
            
            # 设置开始时间
            self.start_time = datetime.now()
            
            current_input = initial_input
            for i, node_id in enumerate(self.node_sequence):
                node = self.nodes[node_id]
                self.previous_node = self.current_node
                self.current_node = node_id
                self.current_node_index = i
                
                logger.info(f"执行节点 {node_id}")
                
                # 通知状态更新
                if self._status_callback:
                    logger.info(f"通知UI更新节点 {node_id} 状态")
                    QTimer.singleShot(0, lambda: self._status_callback(self.get_workflow_status()))
                    await asyncio.sleep(0.2)
                
                try:
                    # 执行节点处理
                    result = await node.process(current_input)
                    logger.info(f"节点 {node_id} 执行完成")
                    
                    # 更新输入数据为当前节点的输出
                    current_input = result
                    
                    # 再次通知状态更新
                    if self._status_callback:
                        logger.info(f"通知UI更新节点 {node_id} 完成状态")
                        QTimer.singleShot(0, lambda: self._status_callback(self.get_workflow_status()))
                        await asyncio.sleep(0.2)
                        
                except Exception as e:
                    logger.error(f"节点 {node_id} 执行失败: {str(e)}")
                    if self._status_callback:
                        QTimer.singleShot(0, lambda: self._status_callback(self.get_workflow_status()))
                        await asyncio.sleep(0.1)
                    raise RuntimeError(f"节点 {node_id} 执行失败: {str(e)}")
                
            # 设置结束时间
            self.end_time = datetime.now()
            return current_input
            
        except Exception as e:
            logger.error(f"工作流执行失败: {str(e)}")
            raise

    def reset_workflow(self) -> None:
        """重置工作流状态"""
        self.current_node_index = -1
        self.current_node = None
        self.previous_node = None
        self.start_time = None
        self.end_time = None
        for node in self.nodes.values():
            node.reset()

    def get_workflow_status(self) -> Dict[str, Any]:
        """获取工作流状态"""
        return {
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "current_node": self.current_node,
            "previous_node": self.previous_node,
            "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            "progress": {
                "current": self.current_node_index + 1,
                "total": len(self.node_sequence)
            }
        }

    def get_node(self, node_id: str) -> Optional[Node]:
        """获取指定节点"""
        return self.nodes.get(node_id)

    def is_completed(self) -> bool:
        """检查工作流是否完成"""
        return all(node.status == NodeStatus.COMPLETED for node in self.nodes.values())

    def has_error(self) -> bool:
        """检查工作流是否有错误"""
        return any(node.status == NodeStatus.ERROR for node in self.nodes.values()) 