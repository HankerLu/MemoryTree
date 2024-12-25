from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QTextEdit, QTabWidget, QScrollArea)
from PyQt5.QtCore import Qt
from typing import Dict, Any
import json

class NodeDetailView(QWidget):
    """节点详情视图"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """设置UI布局"""
        layout = QVBoxLayout(self)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        
        # 基本信息选项卡
        self.basic_info_tab = QWidget()
        basic_layout = QVBoxLayout(self.basic_info_tab)
        
        # 节点ID和名称
        self.id_label = QLabel("节点ID: ")
        self.name_label = QLabel("节点名称: ")
        basic_layout.addWidget(self.id_label)
        basic_layout.addWidget(self.name_label)
        
        # 状态和时间信息
        self.status_label = QLabel("状态: ")
        self.time_label = QLabel("执行时间: ")
        basic_layout.addWidget(self.status_label)
        basic_layout.addWidget(self.time_label)
        
        # 输入数据选项卡
        self.input_tab = QWidget()
        input_layout = QVBoxLayout(self.input_tab)
        self.input_text = QTextEdit()
        self.input_text.setReadOnly(True)
        input_layout.addWidget(self.input_text)
        
        # 原始输出选项卡
        self.raw_output_tab = QWidget()
        raw_output_layout = QVBoxLayout(self.raw_output_tab)
        self.raw_output_text = QTextEdit()
        self.raw_output_text.setReadOnly(True)
        raw_output_layout.addWidget(self.raw_output_text)
        
        # 处理后输出选项卡
        self.processed_output_tab = QWidget()
        processed_output_layout = QVBoxLayout(self.processed_output_tab)
        self.processed_output_text = QTextEdit()
        self.processed_output_text.setReadOnly(True)
        processed_output_layout.addWidget(self.processed_output_text)
        
        # 错误信息选项卡
        self.error_tab = QWidget()
        error_layout = QVBoxLayout(self.error_tab)
        self.error_text = QTextEdit()
        self.error_text.setReadOnly(True)
        error_layout.addWidget(self.error_text)
        
        # 添加所有选项卡
        self.tab_widget.addTab(self.basic_info_tab, "基本信息")
        self.tab_widget.addTab(self.input_tab, "输入数据")
        self.tab_widget.addTab(self.raw_output_tab, "原始输出")
        self.tab_widget.addTab(self.processed_output_tab, "处理后输出")
        self.tab_widget.addTab(self.error_tab, "错误信息")
        
        layout.addWidget(self.tab_widget)
        
    def _format_json(self, data: Any) -> str:
        """格式化JSON数据"""
        try:
            return json.dumps(data, ensure_ascii=False, indent=2)
        except:
            return str(data)
        
    def update_node_info(self, node_data: Dict[str, Any]):
        """更新节点信息显示"""
        # 更新基本信息
        self.id_label.setText(f"节点ID: {node_data.get('node_id', '')}")
        self.name_label.setText(f"节点名称: {node_data.get('node_name', '')}")
        self.status_label.setText(f"状态: {node_data.get('status', '')}")
        
        # 更新时间信息
        start_time = node_data.get('start_time', '')
        end_time = node_data.get('end_time', '')
        time_info = f"开始时间: {start_time}\n结束时间: {end_time}"
        self.time_label.setText(time_info)
        
        # 更新输入数据
        self.input_text.setText(self._format_json(node_data.get('input_data', {})))
        
        # 更新原始输出
        self.raw_output_text.setText(
            self._format_json(node_data.get('output_data', {}).get('raw_output', {}))
        )
        
        # 更新处理后输出
        self.processed_output_text.setText(
            self._format_json(node_data.get('output_data', {}).get('processed_output', {}))
        )
        
        # 更新错误信息
        error_info = node_data.get('error_info', '')
        self.error_text.setText(error_info if error_info else "无错误")
        
        # 如果有错误，自动切换到错误选项卡
        if error_info:
            self.tab_widget.setCurrentWidget(self.error_tab)
    
    def clear(self):
        """清空所有显示"""
        self.id_label.setText("节点ID: ")
        self.name_label.setText("节点名称: ")
        self.status_label.setText("状态: ")
        self.time_label.setText("执行时间: ")
        self.input_text.clear()
        self.raw_output_text.clear()
        self.processed_output_text.clear()
        self.error_text.clear() 