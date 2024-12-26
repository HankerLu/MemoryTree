from PyQt5.QtCore import QThread, pyqtSignal, QMetaObject, Qt
from typing import Dict, Any
import asyncio
import logging

logger = logging.getLogger(__name__)

class WorkflowThread(QThread):
    # 定义信号
    status_updated = pyqtSignal(dict)  # 状态更新信号
    workflow_completed = pyqtSignal(dict)  # 工作流完成信号
    workflow_error = pyqtSignal(str)  # 错误信号
    
    def __init__(self, workflow_manager, initial_input):
        super().__init__()
        self.workflow_manager = workflow_manager
        self.initial_input = initial_input
        
    def _on_status_update(self, status: Dict[str, Any]):
        """状态更新回调，发送信号"""
        logger.info("发送状态更新信号")
        # 确保在主线程中发送信号
        QMetaObject.invokeMethod(self,
                                "status_updated.emit",
                                Qt.QueuedConnection,
                                Q_ARG(dict, status))
        
    def run(self):
        """在单独线程中运行工作流"""
        try:
            logger.info("工作流线程开始运行")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 设置状态更新回调
            self.workflow_manager.set_status_callback(self._on_status_update)
            
            # 执行工作流
            result = loop.run_until_complete(
                self.workflow_manager.execute_workflow(self.initial_input)
            )
            
            logger.info("工作流执行完成，发送完成信号")
            # 发送完成信号
            self.workflow_completed.emit(result)
            
        except Exception as e:
            logger.error(f"工作流执行失败: {str(e)}")
            # 发送错误信号
            self.workflow_error.emit(str(e))
        finally:
            loop.close() 