from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                           QSplitter, QMessageBox, QDialog)
from PyQt5.QtCore import Qt, pyqtSlot, QTimer
from typing import Dict, Any, Optional
from .workflow_view import WorkflowView
from .node_detail_view import NodeDetailView
from .input_dialog import InputDialog
from workflow.core.workflow_manager import WorkflowManager
from workflow.core.node_types import (ConversationNode, NarrativeNode, 
                                    AnalysisNode, SVGNode)
import asyncio

class MonitorWindow(QMainWindow):
    """工作流监控主窗口"""
    
    def __init__(self, initial_input=None, parent=None):
        super().__init__(parent)
        self.workflow_manager = WorkflowManager()
        self.initial_input = initial_input
        self._setup_workflow()
        self._setup_ui()
        self._setup_connections()
        
        # 如果有初始输入，自动开始执行
        if self.initial_input:
            QTimer.singleShot(0, self._auto_start)
        
    def _setup_workflow(self):
        """初始化工作流程"""
        # 添加工作流节点
        self.workflow_manager.add_node("conversation", "对话节点", 
                                     ConversationNode()._process)
        self.workflow_manager.add_node("narrative", "叙事体生成", 
                                     NarrativeNode()._process)
        self.workflow_manager.add_node("analysis", "综合分析", 
                                     AnalysisNode()._process)
        self.workflow_manager.add_node("svg", "SVG卡片生成", 
                                     SVGNode()._process)
        
        # 设置状态更新回调
        self.workflow_manager.set_status_callback(self._on_workflow_status_update)
        
    def _setup_ui(self):
        """设置UI布局"""
        self.setWindowTitle("记忆树工作流监控")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QSplitter::handle {
                background-color: #e0e0e0;
            }
            QPushButton {
                padding: 5px 15px;
                border-radius: 3px;
                background-color: #2196f3;
                color: white;
            }
            QPushButton:disabled {
                background-color: #bbdefb;
            }
        """)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建水平分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧工作流视图
        self.workflow_view = WorkflowView()
        splitter.addWidget(self.workflow_view)
        
        # 右侧节点详情视图
        self.detail_view = NodeDetailView()
        splitter.addWidget(self.detail_view)
        
        # 设置分割比例
        splitter.setSizes([400, 800])
        
        # 设置主布局
        layout = QHBoxLayout(central_widget)
        layout.addWidget(splitter)
        
        # 添加节点到工作流视图
        for node_id, node in self.workflow_manager.nodes.items():
            self.workflow_view.add_node(node_id, node.node_name)
            
    def _setup_connections(self):
        """设置信号连接"""
        # 节点选择
        self.workflow_view.node_selected.connect(self._on_node_selected)
        
        # 开始按钮
        self.workflow_view.start_button.clicked.connect(self._on_start_clicked)
        
        # 重置按钮
        self.workflow_view.reset_button.clicked.connect(self._on_reset_clicked)
        
    @pyqtSlot(str)
    def _on_node_selected(self, node_id: str):
        """处理节点选择事件"""
        node = self.workflow_manager.get_node(node_id)
        if node:
            self.detail_view.update_node_info(node.to_dict())
            
    @pyqtSlot()
    def _on_start_clicked(self, skip_input=False):
        """处理开始按钮点击事件"""
        try:
            if not skip_input:
                # 获取用户输入
                dialog = InputDialog(self)
                if dialog.exec_() != QDialog.Accepted:
                    return
                
                user_input = dialog.get_input()
                if not user_input.strip():
                    QMessageBox.warning(self, "输入错误", "请输入故事内容")
                    return
                
                initial_input = {
                    "user_input": user_input,
                    "conversation_history": [
                        {"role": "user", "content": user_input}
                    ]
                }
            else:
                initial_input = self.initial_input

            # 禁用开始按钮
            self.workflow_view.start_button.setEnabled(False)
            
            # 获取当前运行的事件循环
            loop = asyncio.get_event_loop()
            
            # 使用asyncio.create_task创建异步任务
            future = asyncio.ensure_future(self.workflow_manager.execute_workflow(initial_input))
            
            # 使用QTimer定期检查任务状态
            def check_future():
                if future.done():
                    timer.stop()
                    self.workflow_view.start_button.setEnabled(True)
                    try:
                        future.result()  # 获取结果，如果有错误会抛出
                    except Exception as e:
                        QMessageBox.critical(
                            self,
                            "执行错误",
                            f"工作流执行过程中发生错误：\n{str(e)}"
                        )
            
            timer = QTimer()
            timer.timeout.connect(check_future)
            timer.start(50)  # 每50ms检查一次
            
        except Exception as e:
            # 处理错误
            QMessageBox.critical(
                self,
                "执行错误",
                f"工作流执行过程中发生错误：\n{str(e)}"
            )
        
    @pyqtSlot()
    def _on_reset_clicked(self):
        """处理重置按钮点击事件"""
        self.workflow_manager.reset_workflow()
        self.detail_view.clear()
        self._on_workflow_status_update(self.workflow_manager.get_workflow_status())
        
    def _on_workflow_status_update(self, status: Dict[str, Any]):
        """处理工作流状态更新"""
        self.workflow_view.update_workflow_status(status)
        
        # 如果有当前选中的节点，更新其详情
        current_node = status.get("current_node")
        if current_node:
            node_data = status["nodes"].get(current_node)
            if node_data:
                self.detail_view.update_node_info(node_data) 
        
    def _auto_start(self):
        """自动开始执行工作流"""
        self._on_start_clicked(skip_input=True) 