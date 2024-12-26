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
from workflow.core.workflow_thread import WorkflowThread
import asyncio
import logging

logger = logging.getLogger(__name__)

class MonitorWindow(QMainWindow):
    """工作流监控主窗口"""
    
    def __init__(self, initial_input=None, parent=None):
        super().__init__(parent)
        self.workflow_manager = WorkflowManager()
        self.initial_input = initial_input
        self.user_selected_node = None  # 用户手动选择的节点
        self._setup_workflow()
        self._setup_ui()
        self._setup_connections()
        
        # 如果有初始输入，自动开始执行
        if self.initial_input:
            # 延迟启动以确保界面完全初始化
            QTimer.singleShot(1000, self._auto_start)
        
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
        self.workflow_view.reset_clicked.connect(self._on_reset_clicked)
        
    @pyqtSlot(str)
    def _on_node_selected(self, node_id: str):
        """处理节点选择事件"""
        logger.info(f"用户选择节点: {node_id}")
        self.user_selected_node = node_id  # 记录用户选择
        node = self.workflow_manager.get_node(node_id)
        if node:
            self.detail_view.update_node_info(node.to_dict())
            
    @pyqtSlot()
    def _on_start_clicked(self, skip_input=False):
        """处理开始按钮点击事件"""
        try:
            logger.info("开始执行工作流按钮被点击")
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

            # 创建并启动工作流线程
            self.workflow_thread = WorkflowThread(self.workflow_manager, initial_input)
            # 确保在主线程中连接信号
            self.workflow_thread.status_updated.connect(
                self._on_workflow_status_update, 
                type=Qt.QueuedConnection
            )
            self.workflow_thread.workflow_completed.connect(
                self._on_workflow_completed,
                type=Qt.QueuedConnection
            )
            self.workflow_thread.workflow_error.connect(
                self._on_workflow_error,
                type=Qt.QueuedConnection
            )
            
            logger.info("准备执行工作流")
            self.workflow_thread.start()
            
        except Exception as e:
            logger.error(f"启动工作流失败: {str(e)}")
            QMessageBox.critical(
                self,
                "执行错误",
                f"工作流执行过程中发生错误：\n{str(e)}"
            )
        
    @pyqtSlot()
    def _on_reset_clicked(self):
        """处理重置按钮点击事件"""
        try:
            # 重置工作流管理器
            self.workflow_manager.reset_workflow()
            
            # 清空节点详情视图
            self.detail_view.clear()
            
            # 清除用户选择的节点
            self.user_selected_node = None
            
            # 更新工作流状态显示
            self._on_workflow_status_update(self.workflow_manager.get_workflow_status())
            
            # 重新启用开始按钮
            self.workflow_view.start_button.setEnabled(True)
            
            # 如果是从API启动的，清除初始输入
            self.initial_input = None
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "重置错误",
                f"重置工作流时发生错误：\n{str(e)}"
            )
        
    def _on_workflow_status_update(self, status: Dict[str, Any]):
        """处理工作流状态更新"""
        logger.info(f"收到工作流状态更新: {status}")
        self.workflow_view.update_workflow_status(status)
        
        # 获取当前执行的节点
        current_node = status.get("current_node")
        previous_node = status.get("previous_node")
        logger.info(f"当前执行节点: {current_node}, 前一个节点: {previous_node}")
        
        # 总是显示当前执行的节点，除非用户手动选择了其他节点
        if current_node and not self.user_selected_node:
            logger.info(f"更新详情视图为当前执行节点: {current_node}")
            node_data = status["nodes"].get(current_node)
            if node_data:
                logger.info(f"节点数据: {node_data}")
                self.detail_view.update_node_info(node_data)
                # 强制更新界面
                self.detail_view.repaint()
        # 如果有用户选择的节点，显示用户选择的节点
        elif self.user_selected_node:
            logger.info(f"显示用户选择的节点: {self.user_selected_node}")
            node_data = status["nodes"].get(self.user_selected_node)
            if node_data:
                logger.info(f"节点数据: {node_data}")
                self.detail_view.update_node_info(node_data)
                # 强制更新界面
                self.detail_view.repaint()
        # 如果没有当前节点也没有用户选择的节点，显示第一个节点
        elif not self.user_selected_node:
            first_node = self.workflow_manager.node_sequence[0]
            node_data = status["nodes"].get(first_node)
            if node_data:
                logger.info(f"显示第一个节点: {first_node}")
                self.detail_view.update_node_info(node_data)
                self.detail_view.repaint()
        
    @pyqtSlot(dict)
    def _on_workflow_completed(self, result: Dict[str, Any]):
        """处理工作流完成"""
        logger.info("工作流执行完成")
        self.workflow_view.start_button.setEnabled(True)
        QMessageBox.information(self, "完成", "工作流执行完成")
        
    @pyqtSlot(str)
    def _on_workflow_error(self, error_msg: str):
        """处理工作流错误"""
        logger.error(f"工作流执行失败: {error_msg}")
        self.workflow_view.start_button.setEnabled(True)
        QMessageBox.critical(self, "错误", f"工作流执行失败:\n{error_msg}")
        
    @pyqtSlot()
    def _auto_start(self):
        """自动开始执行工作流"""
        try:
            logger.info("开始自动执行工作流")
            logger.info(f"初始输入: {self.initial_input}")
            self._on_start_clicked(skip_input=True)
        except Exception as e:
            logger.error(f"自动执行失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"自动执行失败: {str(e)}") 