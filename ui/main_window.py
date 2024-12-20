from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QTextEdit, QLabel, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt
import json
import os
from agents.conversation_agent import ConversationAgent
from agents.narrative_agent import NarrativeAgent
from datetime import datetime
from agents.sentence_analyzer_agent import SentenceAnalyzerAgent
from agents.tag_analyzer_agent import TagAnalyzerAgent
from typing import Optional, List, Dict
from database.base import get_db
from services.conversation_service import ConversationService
from services.narrative_service import NarrativeService
from services.paragraph_service import ParagraphService
from services.tag_service import TagService
from entities.narrative import Narrative
from entities.paragraph import Paragraph
from entities.tag import Tag

class MainWindow(QMainWindow):
    def __init__(self, conversation_agent):
        super().__init__()
        self.conversation_agent = conversation_agent
        self.narrative_agent = NarrativeAgent()
        self.sentence_analyzer = SentenceAnalyzerAgent()
        self.tag_analyzer = TagAnalyzerAgent()
        
        # 初始化服务
        self.conversation_service = ConversationService()
        self.narrative_service = NarrativeService()
        self.paragraph_service = ParagraphService()
        self.tag_service = TagService()
        
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
        
        button_layout = QHBoxLayout()
        clear_button = QPushButton("清空界面")
        persist_button = QPushButton("持久化信息")
        send_button = QPushButton("发送")
        
        clear_button.clicked.connect(self.clear_all)
        persist_button.clicked.connect(self.persist_info)
        send_button.clicked.connect(self.send_message)
        
        button_layout.addWidget(clear_button)
        button_layout.addWidget(persist_button)
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
        
        # 析区域
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        analyze_button = QPushButton("分析段落")
        analyze_button.clicked.connect(self.analyze_sentences)
        
        # 添加段落分析的导入和保存按钮
        sentence_button_layout = QHBoxLayout()
        import_sentence_button = QPushButton("导入文本")
        save_sentence_button = QPushButton("保存分析")
        import_sentence_button.clicked.connect(self.import_sentence_text)
        save_sentence_button.clicked.connect(self.save_sentence_analysis)
        sentence_button_layout.addWidget(analyze_button)
        sentence_button_layout.addWidget(import_sentence_button)
        sentence_button_layout.addWidget(save_sentence_button)
        
        # 标签分析区域
        self.tag_analysis_text = QTextEdit()
        self.tag_analysis_text.setReadOnly(True)
        analyze_tags_button = QPushButton("分析标签")
        analyze_tags_button.clicked.connect(self.analyze_tags)
        
        # 添加标签分析的导入和保存按钮
        tag_button_layout = QHBoxLayout()
        import_tags_button = QPushButton("导入文本")
        save_tags_button = QPushButton("保存分析")
        import_tags_button.clicked.connect(self.import_tags_text)
        save_tags_button.clicked.connect(self.save_tags_analysis)
        tag_button_layout.addWidget(analyze_tags_button)
        tag_button_layout.addWidget(import_tags_button)
        tag_button_layout.addWidget(save_tags_button)
        
        right_layout.addWidget(QLabel("叙事体区域"))
        right_layout.addWidget(self.narrative_text)
        
        # 创建叙事体按钮的水平布局
        narrative_button_layout = QHBoxLayout()
        generate_narrative_button = QPushButton("生成叙事体")
        analyze_current_chat_button = QPushButton("分析当前对话")
        save_narrative_button = QPushButton("保存叙事体")
        
        generate_narrative_button.clicked.connect(self.generate_narrative)
        analyze_current_chat_button.clicked.connect(self.analyze_current_chat)
        save_narrative_button.clicked.connect(self.save_narrative)
        
        narrative_button_layout.addWidget(generate_narrative_button)
        narrative_button_layout.addWidget(analyze_current_chat_button)
        narrative_button_layout.addWidget(save_narrative_button)
        
        right_layout.addLayout(narrative_button_layout)
        
        right_layout.addWidget(QLabel("段落分析结果"))
        right_layout.addWidget(self.analysis_text)
        right_layout.addLayout(sentence_button_layout)
        right_layout.addWidget(QLabel("标签分析结果"))
        right_layout.addWidget(self.tag_analysis_text)
        right_layout.addLayout(tag_button_layout)
        
        # 设置左右布局比例
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 1)
        
        # 添加变量保存分析结果
        self.current_paragraphs = None  # 保存当前段落分析结果
        self.current_tag_data = None    # 保存当前标签分析结果
        
    def send_message(self):
        """发送消息的槽函数"""
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
    
    def clear_all(self):
        """清空所有区域的内容并初始化"""
        try:
            # 清空对话区域
            self.chat_history.clear()
            self.input_box.clear()
            
            # 清空叙事体区域
            self.narrative_text.clear()
            
            # 清空分析结果区域
            self.analysis_text.clear()
            self.tag_analysis_text.clear()
            
            # 清空代理中的历史
            self.conversation_agent.clear_history()
            
            # 清空分析结果
            self.current_paragraphs = None
            self.current_tag_data = None
            
            # 显示成功消息
            self.show_info("成功", "所有内容已清空")
        except Exception as e:
            self.show_error(f"清空内容时发生错误：{str(e)}")
    
    def persist_info(self):
        """持久化信息的槽函数"""
        try:
            # 1. 前置检查
            chat_history = self.conversation_agent.get_conversation_history()
            if not chat_history:
                self.show_error("对话历史为空")
                return
            
            narrative_content = self.narrative_text.toPlainText().strip()
            if not narrative_content:
                self.show_error("叙事体内容为空")
                return
            
            merged_results = self.merge_analysis_results()
            if not merged_results:
                self.show_error("分析结果为空或合并失败")
                return
            
            # 2. 生成会话ID
            session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 3. 在事务中执行所有持久化操作
            with get_db() as db:
                try:
                    # 设置所有服务使用同一个会话
                    self.conversation_service._session = db
                    self.narrative_service._session = db
                    self.paragraph_service._session = db
                    self.tag_service._session = db
                    
                    # 3.1 保存对话历史
                    if not self.conversation_service.save_history(session_id, chat_history):
                        raise Exception("保存对话历史失败")
                    
                    # 3.2 保存叙事体
                    narrative = Narrative(
                        session_id=session_id,
                        content=narrative_content
                    )
                    narrative = self.narrative_service.create(narrative)
                    
                    # 3.3 保存段落和标签
                    for idx, result in enumerate(merged_results, 1):
                        # 创建段落
                        paragraph = Paragraph(
                            narrative_id=narrative.id,
                            content=result['content'],
                            sequence_number=idx,
                            paragraph_type=result['type']
                        )
                        paragraph = self.paragraph_service.create(paragraph)
                        
                        # 处理标签
                        for dimension, tags in result['tags'].items():
                            for tag_value in tags:
                                # 查找或创建标签
                                existing_tag = self.tag_service.find_by_dimension_and_value(
                                    dimension, tag_value
                                )
                                if existing_tag:
                                    tag = existing_tag
                                else:
                                    tag = Tag(dimension=dimension, tag_value=tag_value)
                                    tag = self.tag_service.create(tag)
                                
                                # 关联标签
                                paragraph.tags.append(tag)
                        
                        # 更新段落
                        self.paragraph_service.update(paragraph)
                    
                    # 提交事务
                    db.commit()
                    self.show_info("成功", "所有信息已成功持久化")
                    
                except Exception as e:
                    db.rollback()  # 回滚事务
                    raise
                
        except Exception as e:
            self.show_error(f"持久化过程发生错误：{str(e)}")
    
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
        # 获取叙事体文本框中的内容
        narrative_text = self.narrative_text.toPlainText().strip()
        
        if not narrative_text:
            self.show_error("叙事体内容为空，无法保存！")
            return
        
        # 创建保存目录
        save_dir = os.path.join("logs", "content")
        os.makedirs(save_dir, exist_ok=True)
        
        # 生成带时间戳的文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = f"narrative_{timestamp}.txt"
        file_path = os.path.join(save_dir, file_name)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(narrative_text)
            self.show_info("成功", f"叙事体已成功保存到：{file_path}")
        except Exception as e:
            self.show_error(f"保存文件时发生错误：{str(e)}")
    
    def analyze_sentences(self):
        """分析段落的槽函数"""
        narrative = self.narrative_text.toPlainText().strip()
        if not narrative:
            self.show_error("请先生成或输入叙事体")
            return
        
        try:
            # 获取原始分析结果
            analysis = self.sentence_analyzer.analyze_narrative(narrative)
            if analysis.startswith("发生错误"):
                self.show_error(analysis)
                return
            
            # 解析段落结果并保存
            self.current_paragraphs = self.sentence_analyzer.get_paragraphs(analysis)
            
            # 格式化显示结果
            formatted_result = []
            for p in self.current_paragraphs:
                formatted_result.append(f"段落内容：\n{p['text']}\n")
                formatted_result.append(f"段落类型：{p['type']}\n")
                formatted_result.append("-" * 50 + "\n")
            
            # 在分析结果文本框中显示
            self.analysis_text.setText("".join(formatted_result))
            
        except Exception as e:
            self.current_paragraphs = None
            self.show_error(f"分析段落时发生错误：{str(e)}")
    
    def analyze_tags(self):
        """分析标签的槽函数"""
        narrative = self.narrative_text.toPlainText().strip()
        if not narrative:
            self.show_error("叙事体内容为空，无法进行标签分析！")
            return
        
        try:
            # 获取原始分析结果
            tag_result = self.tag_analyzer.analyze_tags(narrative)
            if tag_result.startswith("标签分析出错"):
                self.show_error(tag_result)
                return
            
            # 解析标签结果并保存
            self.current_tag_data = self.tag_analyzer.parse_tags(tag_result)
            
            # 格式化显示结果
            formatted_result = []
            for p in self.current_tag_data:
                formatted_result.append(f"段落内容：\n{p['text']}\n")
                formatted_result.append("标签信息：\n")
                for dimension, tags in p.get('tags', {}).items():
                    if tags and tags != ["无明确体现"]:
                        formatted_result.append(f"{dimension}：{', '.join(tags)}\n")
                formatted_result.append("-" * 50 + "\n")
            
            # 在标签分析文本框中显示结果
            self.tag_analysis_text.setText("".join(formatted_result))
            
        except Exception as e:
            self.current_tag_data = None
            self.show_error(f"分析标签时发生错误：{str(e)}")
    
    def _format_tag_results(self, tag_result):
        """格式化标签析结果"""
        # 直接显示原始结果，保持AI返回的格式
        return tag_result
    
    def show_error(self, message):
        """显示错误消息"""
        QMessageBox.critical(self, "错误", message)
    
    def show_info(self, title, message):
        """显示信息消息"""
        QMessageBox.information(self, title, message)
    
    def import_sentence_text(self):
        """导入文本进行段落分析"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择文本文件",
            "",
            "文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    text = file.read()
                self.narrative_text.setText(text)
                # 自动进行段落分析
                self.analyze_sentences()
            except Exception as e:
                self.show_error(f"导入文件时发生错误：{str(e)}")
    
    def save_sentence_analysis(self):
        """保存段落分析结果"""
        analysis_text = self.analysis_text.toPlainText().strip()
        
        if not analysis_text:
            self.show_error("没有可保存的分析结果！")
            return
        
        # 创建保存目录
        save_dir = os.path.join("logs", "analyze_sentence")
        os.makedirs(save_dir, exist_ok=True)
        
        # 生成带时间戳的文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = f"sentence_analysis_{timestamp}.txt"
        file_path = os.path.join(save_dir, file_name)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(analysis_text)
            self.show_info("成功", f"段落分析结果已保存到：{file_path}")
        except Exception as e:
            self.show_error(f"保存文件时发生错误：{str(e)}")
    
    def import_tags_text(self):
        """导入文本进行标签分析"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择文本文件",
            "",
            "文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    text = file.read()
                self.analysis_text.setText(text)
                # 自动进行标签分析
                self.analyze_tags()
            except Exception as e:
                self.show_error(f"导入文件时发生错误：{str(e)}")
    
    def save_tags_analysis(self):
        """保存标签分析结果"""
        tag_analysis_text = self.tag_analysis_text.toPlainText().strip()
        
        if not tag_analysis_text:
            self.show_error("没有可保存的标签分析结果！")
            return
        
        # 创建保存目录
        save_dir = os.path.join("logs", "analyze_tags")
        os.makedirs(save_dir, exist_ok=True)
        
        # 生成带时间戳的文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = f"tag_analysis_{timestamp}.txt"
        file_path = os.path.join(save_dir, file_name)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(tag_analysis_text)
            self.show_info("成功", f"标签分析结果已保存到：{file_path}")
        except Exception as e:
            self.show_error(f"保存文件时发生错误：{str(e)}")
    
    def analyze_current_chat(self):
        """分析当前对话生成叙事体的槽函数"""
        try:
            # 获取当前对话历史
            chat_history = self.conversation_agent.get_conversation_history()
            
            if not chat_history:
                self.show_error("当前对话历史为空，无法生成叙事体")
                return
            
            # 使用 narrative_agent 生成叙事体
            narrative = self.narrative_agent.generate_narrative(chat_history)
            
            # 在叙事体文本框中显示结果
            self.narrative_text.setText(narrative)
            
        except Exception as e:
            self.show_error(f"分析当前对话时发生错误：{str(e)}")
    
    def merge_analysis_results(self) -> Optional[List[Dict]]:
        """合并段落分析和标签分析的结果"""
        try:
            # 检查是否已有分析结果
            if not self.current_paragraphs or not self.current_tag_data:
                self.show_error("请先进行段落分析和标签分析")
                return None
            
            # 直接使用已有的分析结果
            merged_results = []
            for p, t in zip(self.current_paragraphs, self.current_tag_data):
                merged_results.append({
                    'content': p['text'],
                    'type': p['type'],
                    'tags': t.get('tags', {})
                })
            
            if not merged_results:
                self.show_error("合并结果为空")
                return None
            
            return merged_results
            
        except Exception as e:
            self.show_error(f"合并分析结果时发生错误：{str(e)}")
            return None