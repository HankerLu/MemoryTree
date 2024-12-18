import sys
import signal
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from ui.main_window import MainWindow
from agents.conversation_agent import ConversationAgent
from agents.narrative_agent import NarrativeAgent
from agents.sentence_analyzer_agent import SentenceAnalyzerAgent

class MemoryTreeApp:
    def __init__(self):
        # 在创建 QApplication 之前设置信号处理
        signal.signal(signal.SIGINT, signal.SIG_DFL)  # 恢复默认的 SIGINT 处理
        
        # 初始化各个Agent
        self.conversation_agent = ConversationAgent()
        self.narrative_agent = NarrativeAgent()
        self.sentence_analyzer = SentenceAnalyzerAgent()
        
        self.app = QApplication(sys.argv)
        self.window = MainWindow(self.conversation_agent)
        
        # 设置定时器来检查信号
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_signal)
        self.timer.start(500)  # 每500毫秒检查一次
        
        # 连接信号和槽
        self.setup_connections()
        
    def check_signal(self):
        """定期检查是否收到退出信号"""
        try:
            # 尝试处理待处理的事件
            QApplication.processEvents()
        except KeyboardInterrupt:
            print("\n正在退出程序...")
            self.app.quit()
        
    def setup_connections(self):
        """设置信号和槽的连接"""
        # 发送消息
        def on_send_message():
            user_input = self.window.input_box.toPlainText().strip()
            if not user_input:
                return
                
            # 显示用户输入
            self.window.chat_history.append(f"用户: {user_input}")
            self.window.input_box.clear()
            
            # 获取AI响应
            response = self.conversation_agent.chat(user_input)
            self.window.chat_history.append(f"助手: {response}")
        
        # 清空对话
        def on_clear_chat():
            self.window.chat_history.clear()
            self.conversation_agent.clear_history()
        
        # 生成叙事体
        def on_generate_narrative():
            conversation_history = self.conversation_agent.get_conversation_history()
            if not conversation_history:
                self.window.show_error("对话历史为空，无法生成叙事体")
                return
                
            narrative = self.narrative_agent.generate_narrative(conversation_history)
            self.window.narrative_text.setText(narrative)
        
        # 分析句子
        def on_analyze_sentences():
            narrative = self.window.narrative_text.toPlainText().strip()
            if not narrative:
                self.window.show_error("请先生成或输入叙事体")
                return
                
            analysis = self.sentence_analyzer.analyze_narrative(narrative)
            self.window.analysis_text.setText(analysis)
        
        # 保存叙事体
        def on_save_narrative():
            narrative = self.window.narrative_text.toPlainText().strip()
            if not narrative:
                self.window.show_error("没有可保存的叙事体")
                return
                
            file_name, _ = QFileDialog.getSaveFileName(
                self.window,
                "保存叙事体",
                "",
                "文本文件 (*.txt);;所有文件 (*.*)"
            )
            
            if file_name:
                try:
                    with open(file_name, 'w', encoding='utf-8') as f:
                        f.write(narrative)
                except Exception as e:
                    self.window.show_error(f"保存文件时发生错误：{str(e)}")
        
        # 连接信号和槽
        self.window.send_message = on_send_message
        self.window.clear_chat = on_clear_chat
        self.window.generate_narrative = on_generate_narrative
        self.window.analyze_sentences = on_analyze_sentences
        self.window.save_narrative = on_save_narrative
    
    def run(self):
        """运行应用程序"""
        self.window.show()
        return self.app.exec_()

if __name__ == "__main__":
    app = MemoryTreeApp()
    sys.exit(app.run())
