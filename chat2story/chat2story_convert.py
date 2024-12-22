import os
import zhipuai
from dotenv import load_dotenv
import re
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QTextEdit, QProgressBar, QLabel, QHBoxLayout, QFileDialog
from PyQt5.QtCore import QThread, pyqtSignal
import textwrap
import svgwrite
import markdown
from bs4 import BeautifulSoup

class ConvertThread(QThread):
    """转换处理线程"""
    progress_signal = pyqtSignal(str)  # 进度信息信号
    progress_value = pyqtSignal(int)   # 进度条信号
    finished_signal = pyqtSignal(bool) # 完成信号

    def __init__(self, converter):
        super().__init__()
        self.converter = converter
        
        # 重写converter的打印和进度更新函数
        def new_print(msg):
            self.progress_signal.emit(str(msg))
        def update_progress(value):
            self.progress_value.emit(value)
            
        self.converter.print = new_print
        self.converter.update_progress = update_progress

    def run(self):
        success = self.converter.convert()
        self.finished_signal.emit(success)

class BookGenerator:
    """书籍生成器类"""
    def __init__(self):
        self.page_width = 800
        self.page_height = 1000
        self.margin = 50
        self.line_height = 25
        self.chars_per_line = 30
        self.lines_per_page = 30
        
    def create_page(self, text, page_num):
        """创建单个页面的SVG"""
        # 创建SVG对象
        dwg = svgwrite.Drawing(size=(self.page_width, self.page_height))
        
        # 添加背景
        dwg.add(dwg.rect(insert=(0, 0), size=('100%', '100%'), 
                        fill='#f8f9fa', stroke='#dee2e6', stroke_width=2))
        
        # 添加装饰边框
        dwg.add(dwg.rect(insert=(self.margin/2, self.margin/2), 
                        size=(self.page_width-self.margin, self.page_height-self.margin),
                        fill='none', stroke='#adb5bd', stroke_width=1))
        
        # 添加页码
        dwg.add(dwg.text(f'- {page_num} -', 
                        insert=(self.page_width/2, self.page_height-self.margin/2),
                        font_size=16, text_anchor='middle'))
        
        # 分行处理文本
        lines = textwrap.wrap(text, width=self.chars_per_line)
        
        # 添加文本内容
        for i, line in enumerate(lines[:self.lines_per_page]):
            y = self.margin + (i+1) * self.line_height
            dwg.add(dwg.text(line, insert=(self.margin, y), 
                           font_size=18, font_family='SimSun'))
            
        return dwg

    def generate_book(self, markdown_text, output_dir):
        """生成整本书"""
        # 将Markdown转换为HTML
        html = markdown.markdown(markdown_text)
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        
        # 按页面大小分割文本
        chars_per_page = self.chars_per_line * self.lines_per_page
        pages = [text[i:i+chars_per_page] for i in range(0, len(text), chars_per_page)]
        
        # 生成每一页的SVG
        for i, page_text in enumerate(pages, 1):
            dwg = self.create_page(page_text, i)
            dwg.saveas(f"{output_dir}/page_{i:03d}.svg")
            
        return len(pages)

class GenerateBookThread(QThread):
    """书籍生成线程"""
    progress_signal = pyqtSignal(str)
    progress_value = pyqtSignal(int)
    finished_signal = pyqtSignal(bool)

    def __init__(self, input_file, output_dir):
        super().__init__()
        self.input_file = input_file
        self.output_dir = output_dir
        self.generator = BookGenerator()

    def run(self):
        try:
            # 读取Markdown文件
            self.progress_signal.emit("正在读取Markdown文件...")
            with open(self.input_file, 'r', encoding='utf-8') as f:
                markdown_text = f.read()
            
            # 生成书籍
            self.progress_signal.emit("正在生成SVG页面...")
            pages = self.generator.generate_book(markdown_text, self.output_dir)
            
            self.progress_signal.emit(f"生成完成！共生成 {pages} 页")
            self.finished_signal.emit(True)
            
        except Exception as e:
            self.progress_signal.emit(f"生成过程中发生错误：{str(e)}")
            self.finished_signal.emit(False)

class Chat2StoryGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.converter = Chat2Story()
        
    def initUI(self):
        self.setWindowTitle('访谈转回忆录工具')
        self.setGeometry(300, 300, 800, 600)
        
        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 添加水平布局来放置按钮
        button_layout = QHBoxLayout()
        
        # 开始转换按钮
        self.start_button = QPushButton('开始转换', self)
        self.start_button.clicked.connect(self.start_convert)
        button_layout.addWidget(self.start_button)
        
        # 生成书籍按钮
        self.generate_book_button = QPushButton('生成书籍', self)
        self.generate_book_button.clicked.connect(self.generate_book)
        self.generate_book_button.setEnabled(False)  # 初始时禁用
        button_layout.addWidget(self.generate_book_button)
        
        # 将按钮布局添加到主布局
        layout.addLayout(button_layout)
        
        # 进度条
        self.progress_bar = QProgressBar(self)
        layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel('就绪', self)
        layout.addWidget(self.status_label)
        
        # 日志显示区域
        self.log_text = QTextEdit(self)
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

    def start_convert(self):
        """开始转换"""
        self.start_button.setEnabled(False)
        self.log_text.clear()
        self.progress_bar.setValue(0)
        self.status_label.setText('正在转换...')
        
        # 创建并启动转换线程
        self.convert_thread = ConvertThread(self.converter)
        self.convert_thread.progress_signal.connect(self.update_log)
        self.convert_thread.progress_value.connect(self.progress_bar.setValue)
        self.convert_thread.finished_signal.connect(self.conversion_finished)
        self.convert_thread.start()

    def update_log(self, message):
        """更新日志显示"""
        self.log_text.append(message)
        # 滚动到底部
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def conversion_finished(self, success):
        """转换完成处理"""
        self.start_button.setEnabled(True)
        if success:
            self.status_label.setText('转换完成')
            self.progress_bar.setValue(100)
            self.generate_book_button.setEnabled(True)  # 转换成功后启用生成书籍按钮
        else:
            self.status_label.setText('转换失败')
            self.generate_book_button.setEnabled(False)

    def generate_book(self):
        """生成书籍处理"""
        # 选择输出目录
        output_dir = QFileDialog.getExistingDirectory(self, '选择保存目录')
        if not output_dir:
            return
            
        self.generate_book_button.setEnabled(False)
        self.start_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText('正在生成书籍...')
        
        # 创建并启动生成线程
        self.book_thread = GenerateBookThread('output.md', output_dir)
        self.book_thread.progress_signal.connect(self.update_log)
        self.book_thread.progress_value.connect(self.progress_bar.setValue)
        self.book_thread.finished_signal.connect(self.book_generation_finished)
        self.book_thread.start()

    def book_generation_finished(self, success):
        """书籍生成完成处理"""
        self.generate_book_button.setEnabled(True)
        self.start_button.setEnabled(True)
        if success:
            self.status_label.setText('书籍生成完成')
            self.progress_bar.setValue(100)
        else:
            self.status_label.setText('书籍生成失败')

class Chat2Story:
    def __init__(self):
        # 加载环境变量
        load_dotenv()
        self.api_key = os.getenv("API_KEY_CONF")
        if not self.api_key:
            raise ValueError("未找到API密钥，请检查环境变量 API_KEY_CONF")
        self.client = zhipuai.ZhipuAI(api_key=self.api_key)
        self.print = print  # 可被GUI重写的打印函数
        self.update_progress = lambda x: None  # 可被GUI重写的进度更新函数
        
        # 系统提示词
        self.system_prompt = """你是一位专业的文学创作者。你的任务是将口述访谈内容转换为优美的第一人称叙事文本。

请遵循以下转换原则：
1. 采用第一人称视角，将对话内容重写为回忆录形式
2. 保留原文的情感基调和关键细节
3. 按照时间顺序或逻辑关系组织内容
4. 使用优美流畅的文学性语言
5. 适当添加环境描写和心理描写
6. 保持叙事的连贯性和完整性

示例转换：
访谈原文：
"问：您是什么时候来到这座城市的？
答：那是1980年，我刚大学毕业。来的时候正是夏天，特别热。"

转换后：
"1980年的盛夏，我怀着憧憬来到这座城市。那时我刚从大学毕业，年轻气盛，���未来充满期待。记得那天骄阳似火，但丝毫没有影响我激动的心情。"

请开始转换工作。"""

    def read_interview(self, filename='interview_record.md'):
        """读取访谈记录文件"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.print(f"读取文件时发生错误：{str(e)}")
            return None

    def split_text(self, text, max_length=1000):
        """将长文本分段"""
        self.print("正在分段处理文本...")
        segments = re.split(r'(发言人\d+\s+\d+:\d+\n)', text)
        
        # 合并分割后的片段
        current_segment = ""
        segments_result = []
        
        for i in range(1, len(segments), 2):
            if i+1 < len(segments):
                current_piece = segments[i] + segments[i+1]
                if len(current_segment) + len(current_piece) < max_length:
                    current_segment += current_piece
                else:
                    if current_segment:
                        segments_result.append(current_segment)
                    current_segment = current_piece
        
        if current_segment:
            segments_result.append(current_segment)
        
        self.print(f"文本已分为 {len(segments_result)} 个段落")    
        return segments_result

    def convert_segment(self, segment):
        """转换单个文本段落"""
        try:
            self.print("正在转换段落...")
            self.print("-" * 40)
            self.print(f"段落前100字: {segment[:100]}...")
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"请将以下访谈内容转换为优美的第一人称叙事文：\n\n{segment}"}
            ]
            
            response = self.client.chat.completions.create(
                model="glm-4",
                messages=messages,
                temperature=0.7,
            )
            
            result = response.choices[0].message.content
            self.print(f"转换完成，输出前100字: {result[:100]}...")
            self.print("-" * 40)
            return result
            
        except Exception as e:
            self.print(f"转换段落时发生错误：{str(e)}")
            return None

    def convert(self, input_file='interview_record.md', output_file='output.md'):
        """执行完整的转换流程"""
        self.print(f"\n开始处理文件: {input_file}")
        self.update_progress(0)  # 开始时进度为0
        
        # 读取访谈文本
        self.print("正在读取访谈记录...")
        interview_text = self.read_interview(input_file)
        if not interview_text:
            self.print("读取文件失败！")
            return False
        self.print(f"成功读取文件，总长度: {len(interview_text)} 字符")
        self.update_progress(10)  # 文件读取完成，进度10%
            
        # 分段处理
        segments = self.split_text(interview_text)
        self.update_progress(20)  # 分段完成，进度20%
        
        if not segments:
            self.print("分段处理失败！")
            return False
            
        # 转换每个段落
        converted_segments = []
        self.print("\n开始转换段落...")
        
        # 计算每个段落的进度比例
        segment_progress = 60 / len(segments)  # 段落转换总共占60%的进度(20%-80%)
        
        for i, segment in enumerate(segments, 1):
            self.print(f"\n处理第 {i}/{len(segments)} 个段落")
            converted_text = self.convert_segment(segment)
            if converted_text:
                converted_segments.append(converted_text)
                # 更新进度：20% + 已完成段落数 × 每段进度
                current_progress = 20 + int(i * segment_progress)
                self.update_progress(current_progress)
            else:
                self.print(f"警告：第 {i} 个段落转换失败")
            
        # 合并并保存结果
        try:
            self.print(f"\n正在保存结果到文件: {output_file}")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# 回忆录\n\n")
                f.write("\n\n".join(converted_segments))
            self.print("文件保存成功！")
            self.update_progress(100)  # 完成，进度100%
            return True
        except Exception as e:
            self.print(f"保存文件时发生错误：{str(e)}")
            return False

def main():
    app = QApplication([])
    gui = Chat2StoryGUI()
    gui.show()
    app.exec_()

if __name__ == "__main__":
    main()
