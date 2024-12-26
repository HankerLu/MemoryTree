from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTextEdit, 
                           QScrollArea, QFrame)
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
        # 创建滚动区域
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        
        # 创建主容器
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # 基本信息区域
        basic_info = QFrame()
        basic_info.setFrameStyle(QFrame.Panel | QFrame.Raised)
        basic_layout = QVBoxLayout(basic_info)
        
        self.id_label = QLabel("节点ID: ")
        self.name_label = QLabel("节点名称: ")
        self.status_label = QLabel("状态: ")
        self.time_label = QLabel("执行时间: ")
        
        basic_layout.addWidget(self.id_label)
        basic_layout.addWidget(self.name_label)
        basic_layout.addWidget(self.status_label)
        basic_layout.addWidget(self.time_label)
        layout.addWidget(basic_info)
        
        # 输入数据区域
        input_group = self._create_group("输入数据")
        self.input_text = input_group["text"]
        layout.addWidget(input_group["frame"])
        
        # 原始输出区域
        raw_output_group = self._create_group("原始输出")
        self.raw_output_text = raw_output_group["text"]
        layout.addWidget(raw_output_group["frame"])
        
        # 处理后输出区域
        processed_output_group = self._create_group("处理后输出")
        self.processed_output_text = processed_output_group["text"]
        layout.addWidget(processed_output_group["frame"])
        
        # 错误信息区域
        error_group = self._create_group("错误信息")
        self.error_text = error_group["text"]
        layout.addWidget(error_group["frame"])
        
        # 设置滚动区域的部件
        scroll.setWidget(container)
        
        # 设置主布局
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
        
    def _create_group(self, title: str) -> Dict[str, Any]:
        """创建分组框"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Panel | QFrame.Raised)
        layout = QVBoxLayout(frame)
        
        label = QLabel(title)
        label.setStyleSheet("font-weight: bold;")
        layout.addWidget(label)
        
        text = QTextEdit()
        text.setReadOnly(True)
        text.setMinimumHeight(100)
        layout.addWidget(text)
        
        return {"frame": frame, "text": text}
        
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