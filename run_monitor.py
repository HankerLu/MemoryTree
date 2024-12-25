import sys
import asyncio
import json
import argparse
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from workflow.ui.monitor_window import MonitorWindow

class AsyncHelper:
    """辅助类，用于在Qt中运行异步代码"""
    def __init__(self, app):
        self.app = app
        # 创建新的事件循环
        self.loop = asyncio.new_event_loop()
        # 设置事件循环策略
        if sys.platform.startswith('win'):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        # 确保事件循环在当前线程运行
        asyncio.set_event_loop(self.loop)
        self.loop.set_exception_handler(self._handle_exception)
        
    def _handle_exception(self, loop, context):
        """处理异步代码中的异常"""
        exception = context.get('exception')
        if exception:
            print(f"异步执行错误: {str(exception)}")
    
    def run(self):
        """运行事件循环"""
        def process_events():
            self.loop.stop()
            self.loop.run_forever()
        
        # 创建定时器来处理异步事件
        self.timer = QTimer()
        self.timer.timeout.connect(process_events)
        self.timer.start(10)  # 每10ms处理一次事件

    def stop(self):
        """停止事件循环"""
        if hasattr(self, 'timer'):
            self.timer.stop()
        self.loop.stop()
        self.loop.close()

def main():
    """主函数"""
    try:
        # 解析命令行参数
        parser = argparse.ArgumentParser()
        parser.add_argument("--input", help="初始输入数据文件路径")
        args = parser.parse_args()
        
        # 读取初始输入数据
        initial_input = {}
        if args.input:
            with open(args.input, 'r') as f:
                initial_input = json.load(f)

        # 创建Qt应用
        app = QApplication(sys.argv)
        
        # 创建异步助手
        async_helper = AsyncHelper(app)
        async_helper.run()  # 启动事件循环处理
        
        # 创建并显示监控窗口
        window = MonitorWindow(initial_input)
        window.show()
        
        # 设置退出处理
        app.aboutToQuit.connect(async_helper.stop)
        
        # 运行应用
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"程序启动错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 