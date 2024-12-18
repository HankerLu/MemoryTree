from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QTextEdit, QLabel, QFileDialog, QMessageBox,
                             QDialog)
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import Qt, QByteArray
import json
import os
import subprocess
import platform
from agents.conversation_agent import ConversationAgent
from agents.narrative_agent import NarrativeAgent

class SvgViewerDialog(QDialog):
    def __init__(self, svg_content, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SVG卡片预览")
        self.setModal(True)
        
        # 设置对话框大小
        self.resize(850, 650)
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 创建SVG显示组件
        svg_widget = QSvgWidget()
        svg_widget.load(QByteArray(svg_content.encode()))
        
        # 添加到布局
        layout.addWidget(svg_widget)
        
        # 添加关闭按钮
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

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
        
        # 添加卡片生成按钮
        generate_card_button = QPushButton("卡片生成")
        generate_card_button.clicked.connect(self.generate_card)
        
        # 句子分析区域
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        analyze_button = QPushButton("分析句子")
        analyze_button.clicked.connect(self.analyze_sentences)
        
        right_layout.addWidget(QLabel("叙事体区域"))
        right_layout.addWidget(self.narrative_text)
        right_layout.addWidget(generate_narrative_button)
        right_layout.addWidget(save_narrative_button)
        right_layout.addWidget(generate_card_button)
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
    
    def generate_card(self):
        """生成SVG卡片的槽函数"""
        narrative = self.narrative_text.toPlainText().strip()
        if not narrative:
            self.show_error("没有可生成卡片的叙事体内容")
            return
        
        try:
            # 将文本分段
            paragraphs = narrative.split('\n\n')
            # 生成文本的SVG元素
            text_elements = []
            y_position = 100  # 起始y坐标
            
            for paragraph in paragraphs:
                # 对段落进行换行处理
                words = paragraph.strip().split()
                lines = []
                current_line = []
                current_length = 0
                
                # 简单的文本换行处理
                for word in words:
                    word_length = len(word)
                    if current_length + word_length <= 30:  # 假设每行大约30个字
                        current_line.append(word)
                        current_length += word_length
                    else:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                        current_length = word_length
                
                if current_line:
                    lines.append(' '.join(current_line))
                
                # 生成这个段落的SVG文本元素
                for line in lines:
                    text_elements.append(
                        f'<text x="80" y="{y_position}" '
                        'font-family="Microsoft YaHei, Arial" '
                        'font-size="16" fill="#333">'
                        f'{line}</text>'
                    )
                    y_position += 25  # 行间距
                
                y_position += 15  # 段落间距

            # 生成SVG内容
            svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
    <rect width="100%" height="100%" fill="#f0f0f0"/>
    <rect x="40" y="40" width="720" height="520" fill="white" 
        stroke="#333" stroke-width="2" rx="15"/>
    {chr(10).join(text_elements)}
</svg>'''
            
            # 显示SVG预览对话框
            dialog = SvgViewerDialog(svg_content, self)
            dialog.exec_()
            
            # 询问是否保存文件
            reply = QMessageBox.question(self, '保存文件', 
                                       '是否要保存SVG文件？',
                                       QMessageBox.Yes | QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                # 打开文件保存对话框
                file_name, _ = QFileDialog.getSaveFileName(
                    self,
                    "保存SVG卡片",
                    "cards/",  # 默认保存到cards文件夹
                    "SVG文件 (*.svg);;所有文件 (*.*)"
                )
                
                if file_name:  # 如果用户选择了保存位置
                    # 确保目标目录存在
                    os.makedirs(os.path.dirname(file_name), exist_ok=True)
                    
                    # 保存SVG文件
                    with open(file_name, 'w', encoding='utf-8') as f:
                        f.write(svg_content)
                        
                    QMessageBox.information(self, "成功", "SVG卡片已成功保存！")
                
        except Exception as e:
            self.show_error(f"生成SVG卡片时发生错误：{str(e)}")
    
    def show_error(self, message):
        """显示错误信息"""
        QMessageBox.critical(self, "错误", message) 