from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QPushButton, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from typing import Dict, Any

class NodeWidget(QFrame):
    """单个节点的可视化组件"""
    clicked = pyqtSignal(str)  # 节点点击信号

    def __init__(self, node_id: str, node_name: str, parent=None):
        super().__init__(parent)
        self.node_id = node_id
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setMinimumHeight(80)
        
        # 设置布局
        layout = QVBoxLayout(self)
        
        # 节点名称
        self.name_label = QLabel(node_name)
        self.name_label.setAlignment(Qt.AlignCenter)
        
        # 状态标签
        self.status_label = QLabel("等待中")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.name_label)
        layout.addWidget(self.status_label)
        
        # 设置点击事件
        self.mousePressEvent = lambda e: self.clicked.emit(self.node_id)

    def update_status(self, status: str):
        """更新节点状态"""
        status_map = {
            "waiting": "等待中",
            "running": "执行中",
            "completed": "已完成",
            "error": "错误"
        }
        self.status_label.setText(status_map.get(status, status))
        
        # 根据状态设置样式
        if status == "running":
            self.setStyleSheet("background-color: #e3f2fd;")
        elif status == "completed":
            self.setStyleSheet("background-color: #c8e6c9;")
        elif status == "error":
            self.setStyleSheet("background-color: #ffcdd2;")
        else:
            self.setStyleSheet("")

class WorkflowView(QWidget):
    """工作流视图组件"""
    node_selected = pyqtSignal(str)  # 节点选择信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.nodes = {}  # 存储节点组件
        self._setup_ui()

    def _setup_ui(self):
        """设置UI布局"""
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("工作流程")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 节点容器
        self.nodes_layout = QVBoxLayout()
        layout.addLayout(self.nodes_layout)
        
        # 控制按钮
        self.start_button = QPushButton("开始执行")
        self.reset_button = QPushButton("重置")
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.reset_button)
        layout.addLayout(button_layout)

    def add_node(self, node_id: str, node_name: str):
        """添加节点到视图"""
        node_widget = NodeWidget(node_id, node_name)
        node_widget.clicked.connect(self.node_selected.emit)
        self.nodes[node_id] = node_widget
        self.nodes_layout.addWidget(node_widget)

    def update_node_status(self, node_id: str, status: str):
        """更新节点状态"""
        if node_id in self.nodes:
            self.nodes[node_id].update_status(status)

    def update_workflow_status(self, status: Dict[str, Any]):
        """更新整个工作流状态"""
        for node_id, node_data in status["nodes"].items():
            self.update_node_status(node_id, node_data["status"]) 