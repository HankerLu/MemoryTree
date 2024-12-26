import sys
import asyncio
import json
import argparse
import logging
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from workflow.ui.monitor_window import MonitorWindow
import threading

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('../../monitor.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def exception_hook(exctype, value, tb):
    """全局异常处理"""
    error_msg = ''.join(traceback.format_exception(exctype, value, tb))
    logger.error(f"未捕获的异常:\n{error_msg}")
    QMessageBox.critical(None, "错误", f"发生未捕获的异常:\n{error_msg}")
    sys.__excepthook__(exctype, value, tb)

sys.excepthook = exception_hook

class AsyncHelper:
    """辅助类，用于在Qt中运行异步代码"""
    def __init__(self, app):
        self.app = app
        self.loop = asyncio.new_event_loop()
        if sys.platform.startswith('win'):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.set_event_loop(self.loop)
        self.loop.set_exception_handler(self._handle_exception)
        
    def _handle_exception(self, loop, context):
        """处理异步代码中的异常"""
        exception = context.get('exception')
        if exception:
            logger.error(f"异步执行错误: {str(exception)}")
            QMessageBox.critical(None, "错误", f"异步执行错误: {str(exception)}")
    
    def run(self):
        """运行事件循环"""
        try:
            # 在单独的线程中运行事件循环
            self.loop_thread = threading.Thread(target=self._run_loop, daemon=True)
            self.loop_thread.start()
            
            # 创建定时器来处理UI更新
            def process_events():
                try:
                    if not self.loop.is_closed():
                        self.loop.stop()
                        self.loop.run_forever()
                except Exception as e:
                    logger.error(f"事件处理错误: {str(e)}")
                    QMessageBox.critical(None, "错误", f"事件处理错误: {str(e)}")
            
            self.timer = QTimer()
            self.timer.timeout.connect(process_events)
            self.timer.start(10)
        except Exception as e:
            logger.error(f"事件循环启动错误: {str(e)}")
            QMessageBox.critical(None, "错误", f"事件循环启动错误: {str(e)}")

    def stop(self):
        """停止事件循环"""
        try:
            if hasattr(self, 'timer'):
                self.timer.stop()
            if hasattr(self, 'loop'):
                self.loop.stop()
                self.loop.close()
            if hasattr(self, 'loop_thread'):
                self.loop_thread.join(timeout=1.0)
        except Exception as e:
            logger.error(f"停止事件循环时发生错误: {str(e)}")

    def _run_loop(self):
        """在新线程中运行事件循环"""
        try:
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        except Exception as e:
            logger.error(f"事件循环运行错误: {str(e)}")
            QMessageBox.critical(None, "错误", f"事件循环运行错误: {str(e)}")

def main():
    """主函数"""
    try:
        logger.info("启动监控程序")
        
        # 解析命令行参数
        parser = argparse.ArgumentParser()
        parser.add_argument("--input", help="初始输入数据文件路径")
        args = parser.parse_args()
        
        logger.info(f"输入文件: {args.input}")
        
        # 读取初始输入数据
        initial_input = {}
        if args.input:
            try:
                with open(args.input, 'r', encoding='utf-8') as f:
                    initial_input = json.load(f)
                logger.info(f"读取到初始输入: {initial_input}")
            except Exception as e:
                logger.error(f"读取输入文件失败: {str(e)}")
                QMessageBox.critical(None, "错误", f"读取输入文件失败: {str(e)}")
                return 1

        # 创建Qt应用
        app = QApplication(sys.argv)
        
        # 创建异步助手
        async_helper = AsyncHelper(app)
        async_helper.run()
        
        # 创建并显示监控窗口
        window = MonitorWindow(initial_input)
        window.show()
        logger.info("监控窗口已显示")
        
        # 设置退出处理
        app.aboutToQuit.connect(async_helper.stop)
        
        # 运行应用
        return app.exec_()
        
    except Exception as e:
        error_msg = f"程序启动错误: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        QMessageBox.critical(None, "错误", error_msg)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 