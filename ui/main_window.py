from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QTextEdit, QLabel, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt
import json
import os
from agents.conversation_agent import ConversationAgent
from agents.narrative_agent import NarrativeAgent

class MainWindow(QMainWindow):
    def __init__(self, conversation_agent):
        super().__init__()
        self.conversation_agent = conversation_agent
        self.narrative_agent = NarrativeAgent()
        self.setWindowTitle("记忆树对话系统")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中心部件和主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧对话区域
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        
        self.input_box = QTextEdit()
        self.input_box.setMaximumHeight(100)
        
        send_button = QPushButton("发送")
        send_button.clicked.connect(self.send_message)
        
        clear_button = QPushButton("清空对话")
        clear_button.clicked.connect(self.clear_chat)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(clear_button)
        button_layout.addWidget(send_button)
        
        left_layout.addWidget(QLabel("对话区域"))
        left_layout.addWidget(self.chat_history)
        left_layout.addWidget(QLabel("输入消息"))
        left_layout.addWidget(self.input_box)
        left_layout.addLayout(button_layout)
        
        # 右侧功能区域
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # 叙事体生成区域
        self.narrative_text = QTextEdit()
        generate_narrative_button = QPushButton("生成叙事体")
        generate_narrative_button.clicked.connect(self.generate_narrative)
        
        save_narrative_button = QPushButton("保存叙事体")
        save_narrative_button.clicked.connect(self.save_narrative)
        
        # 句子分析区域
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        analyze_button = QPushButton("分析句子")
        analyze_button.clicked.connect(self.analyze_sentences)
        
        right_layout.addWidget(QLabel("叙事体区域"))
        right_layout.addWidget(self.narrative_text)
        right_layout.addWidget(generate_narrative_button)
        right_layout.addWidget(save_narrative_button)
        right_layout.addWidget(QLabel("句子分析结果"))
        right_layout.addWidget(self.analysis_text)
        right_layout.addWidget(analyze_button)
        
        # 设置左右布局比例
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 1)
        
    def send_message(self):
        """发送消息的槽函数"""
        # 获取用户输入
        user_input = self.input_box.toPlainText().strip()
        if not user_input:
            return
            
        # 在聊天历史中显示用户输入
        self.chat_history.append(f"用户: {user_input}")
        self.input_box.clear()
        
        # 获取AI响应
        try:
            response = self.conversation_agent.chat(user_input)
            self.chat_history.append(f"助手: {response}")
        except Exception as e:
            self.show_error(f"发送消息时发生错误：{str(e)}")
            print(f"发送消息时发生错误：{str(e)}")
    
    def clear_chat(self):
        """清空对话历史的槽函数"""
        pass
    
    def generate_narrative(self):
        """生成叙事体的槽函数"""
        try:
            # 打开文件选择对话框，限定为json文件
            file_name, _ = QFileDialog.getOpenFileName(
                self,
                "选择对话历史文件",
                "logs/",  # 默认打开logs文件夹
                "JSON文件 (*.json);;所有文件 (*.*)"
            )
            
            if not file_name:  # 用户取消选择
                return
            
            # 读取选中的对话历史文件
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    conversation_history = json.load(f)
            except Exception as e:
                self.show_error(f"读取对话历史文件时发生错误：{str(e)}")
                return
            
            if not conversation_history:
                self.show_error("对话历史为空，无法生成叙事体")
                return
            
            # 使用 narrative_agent 生成叙事体
            narrative = self.narrative_agent.generate_narrative(conversation_history)
            
            # 在叙事体文本框中显示结果
            self.narrative_text.setText(narrative)
            
        except Exception as e:
            self.show_error(f"生成叙事体时发生错误：{str(e)}")
    
    def save_narrative(self):
        """保存叙事体的槽函数"""
        # 获取叙事体内容
        narrative = self.narrative_text.toPlainText().strip()
        if not narrative:
            self.show_error("没有可保存的叙事体内容")
            return
            
        # 打开文件保存对话框
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "保存叙事体",
            "narratives/",  # 默认保存到narratives文件夹
            "文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if file_name:  # 如果用户选择了保存位置
            try:
                # 确保目标目录存在
                os.makedirs(os.path.dirname(file_name), exist_ok=True)
                
                # 保存文件
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write(narrative)
                    
                QMessageBox.information(self, "成功", "叙事体已成功保存！")
                
            except Exception as e:
                self.show_error(f"保存文件时发生错误：{str(e)}")
    
    def analyze_sentences(self):
        """分析句子的槽函数"""
        pass
    
    def show_error(self, message):
        """显示错误���息"""
        QMessageBox.critical(self, "错误", message) 