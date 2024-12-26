from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QPushButton, QFrame, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal, QMetaObject
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

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
    """工作流视图"""
    node_selected = pyqtSignal(str)  # 节点选择信号
    reset_clicked = pyqtSignal()     # 重置按钮点击信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.nodes = {}  # 存储节点标签
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
        self.reset_button.clicked.connect(self._on_reset_clicked)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.reset_button)
        layout.addLayout(button_layout)

    def add_node(self, node_id: str, node_name: str):
        """添加节点"""
        label = QLabel(f"{node_name} ({node_id})")
        label.setStyleSheet("""
            QLabel {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #f8f9fa;
                margin: 5px;
            }
        """)
        label.mousePressEvent = lambda e: self.node_selected.emit(node_id)
        
        self.nodes[node_id] = label
        self.nodes_layout.addWidget(label)
        
    def update_workflow_status(self, status: Dict[str, Any]):
        """更新工作流状态显示"""
        logger.info(f"更新工作流视图状态: {status}")
        try:
            # 获取当前节点
            current_node = status.get("current_node")
            nodes_status = status.get("nodes", {})
            
            # 更新所有节点的显示状态
            for node_id, label in self.nodes.items():
                node_status = nodes_status.get(node_id, {})
                status_text = node_status.get("status", "PENDING")
                logger.debug(f"节点 {node_id} 状态: {status_text}")
                
                # 根据状态设置样式
                if node_id == current_node:
                    style = """
                        QLabel {
                            padding: 10px;
                            border: 2px solid #ff9800;
                            border-radius: 5px;
                            background-color: #fff3e0;
                            margin: 5px;
                            font-weight: bold;
                        }
                    """
                elif status_text == "COMPLETED":
                    style = """
                        QLabel {
                            padding: 10px;
                            border: 1px solid #4caf50;
                            border-radius: 5px;
                            background-color: #e8f5e9;
                            margin: 5px;
                        }
                    """
                elif status_text == "ERROR":
                    style = """
                        QLabel {
                            padding: 10px;
                            border: 1px solid #f44336;
                            border-radius: 5px;
                            background-color: #ffebee;
                            margin: 5px;
                        }
                    """
                else:
                    style = """
                        QLabel {
                            padding: 10px;
                            border: 1px solid #ddd;
                            border-radius: 5px;
                            background-color: #f8f9fa;
                            margin: 5px;
                        }
                    """
                
                # 使用 QMetaObject.invokeMethod 确保在主线程中更新 UI
                from PyQt5.QtCore import QMetaObject, Qt
                QMetaObject.invokeMethod(label, 
                                       "setStyleSheet",
                                       Qt.QueuedConnection,
                                       Q_ARG(str, style))
                # 更新节点文本以显示状态
                text = f"{label.text().split(' [')[0]} [{status_text}]"
                QMetaObject.invokeMethod(label,
                                       "setText",
                                       Qt.QueuedConnection,
                                       Q_ARG(str, text))
                
        except Exception as e:
            logger.error(f"更新工作流视图状态失败: {str(e)}")
            raise

    def _on_reset_clicked(self):
        """处理重置按钮点击"""
        # 发送重置信号
        self.reset_clicked.emit()
        # 重置所有节点的样式
        for label in self.nodes.values():
            style = """
                QLabel {
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    background-color: #f8f9fa;
                    margin: 5px;
                }
            """
            label.setStyleSheet(style)
            # 重置节点文本
            text = label.text().split(" [")[0]
            label.setText(text) 