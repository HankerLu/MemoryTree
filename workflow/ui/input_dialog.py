from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
                           QPushButton, QLabel, QMessageBox)
from PyQt5.QtCore import Qt

class InputDialog(QDialog):
    """用户输入对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("开始新的对话")
        self.setMinimumWidth(500)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 提示标签
        prompt = QLabel("请讲述你想要记录的故事或回忆：")
        prompt.setStyleSheet("font-size: 12px; margin-bottom: 10px;")
        layout.addWidget(prompt)
        
        # 输入框
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("在这里输入你的故事...")
        self.input_text.setMinimumHeight(200)
        layout.addWidget(self.input_text)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("开始")
        self.ok_button.setDefault(True)
        self.ok_button.clicked.connect(self.accept)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
    def get_input(self) -> str:
        return self.input_text.toPlainText() 