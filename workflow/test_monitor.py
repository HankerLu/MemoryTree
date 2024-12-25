import sys
import asyncio
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from ui.monitor_window import MonitorWindow

class AsyncHelper:
    """辅助类，用于在Qt中运行异步代码"""
    def __init__(self, app):
        self.app = app
        self.loop = asyncio.get_event_loop()
        self.loop.set_exception_handler(self._handle_exception)
        
    def _handle_exception(self, loop, context):
        """处理异步代码中的异常"""
        exception = context.get('exception')
        if exception:
            print(f"异步执行错误: {str(exception)}")
    
    def run(self):
        """运行事件循环"""
        try:
            self.loop.run_forever()
        finally:
            self.loop.close()
            
    def stop(self):
        """停止事件循环"""
        self.loop.stop()

def main():
    """主函数"""
    try:
        # 创建Qt应用
        app = QApplication(sys.argv)
        
        # 创建异步助手
        async_helper = AsyncHelper(app)
        
        # 创建并显示监控窗口
        window = MonitorWindow()
        window.show()
        
        # 设置退出处理
        app.aboutToQuit.connect(async_helper.stop)
        
        # 启动定时器来处理异步事件
        timer = QTimer()
        timer.timeout.connect(lambda: None)  # 让事件循环继续运行
        timer.start(50)  # 50ms间隔
        
        # 运行应用
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"程序启动错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 