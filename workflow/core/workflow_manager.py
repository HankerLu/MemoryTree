from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from .node import Node, NodeStatus

class WorkflowManager:
    """工作流管理器，负责协调和监控整个工作流程"""
    
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.node_sequence: List[str] = []
        self.current_node_index: int = -1
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
        """执行整个工作流"""
        if not self.nodes:
            raise ValueError("工作流中没有节点")

        try:
            self.start_time = datetime.now()
            current_input = initial_input

            for i, node_id in enumerate(self.node_sequence):
                self.current_node_index = i
                node = self.nodes[node_id]
                
                # 确保在每个节点执行前更新状态
                if self._status_callback:
                    self._status_callback(self.get_workflow_status())

                try:
                    current_input = await node.process(current_input)
                except Exception as e:
                    self.end_time = datetime.now()
                    # 确保在错误发生时也更新状态
                    if self._status_callback:
                        self._status_callback(self.get_workflow_status())
                    raise RuntimeError(f"节点 {node_id} 执行失败: {str(e)}")

            self.end_time = datetime.now()
            # 最终状态更新
            if self._status_callback:
                self._status_callback(self.get_workflow_status())

            return current_input

        except Exception as e:
            self.end_time = datetime.now()
            raise

    def reset_workflow(self) -> None:
        """重置工作流状态"""
        self.current_node_index = -1
        self.start_time = None
        self.end_time = None
        for node in self.nodes.values():
            node.reset()

    def get_workflow_status(self) -> Dict[str, Any]:
        """获取工作流状态"""
        return {
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "current_node": self.node_sequence[self.current_node_index] if self.current_node_index >= 0 else None,
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