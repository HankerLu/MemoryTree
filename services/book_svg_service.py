from dataclasses import dataclass
from typing import List, Optional
from enum import Enum
import re

class ContentType(Enum):
    CHAPTER = "chapter"
    CONTENT = "content"

@dataclass
class BookPageConfig:
    # 页面尺寸
    page_width: int = 595    # A4纸的标准宽度（像素）
    page_height: int = 842   # A4纸的标准高度（像素）
    
    # 边距调整（统一边距）
    margin_top: int = 100
    margin_bottom: int = 80   # 增加下边距
    margin_left: int = 70     # 统一左边距
    margin_right: int = 100    # 统一右边距
    
    # 章节页字体设置
    chapter_number_font_size: int = 24
    chapter_title_font_size: int = 48
    
    # 小节页面设置（增大字号）
    section_number_font_size: int = 28
    section_title_font_size: int = 28
    content_font_size: int = 24         # 增大正文字体
    
    # 行高和间距
    line_height: int = 48              # 行高为字体大小的1.85倍
    paragraph_spacing: int = 10        # 段落间距
    title_spacing: int = 80           # 标题后的间距
    
    # 文本区域设置
    text_width: int = 395             # 595 - (100 * 2)
    chars_per_line: int = 19          # 减少每行字符数，确保不超出右边距
    lines_per_page: int = 15          # 每页行数
    
    # 添加页码字体大小配置
    page_number_font_size: int = 20    # 页码字号，比正文小一点

class BookSVGService:
    def __init__(self):
        self.config = BookPageConfig()
    
    def generate_svg(self, number: str, title: str, content: str = None, is_chapter: bool = False) -> List[str]:
        """统一的生成接口
        :param number: 章节序号（如'Chapter 6'或'第3节'）
        :param title: 标题（如'篮球'）
        :param content: 正文内容（如果是章节页则为None）
        :param is_chapter: 是否是章节页
        """
        if is_chapter:
            return self._generate_chapter_svg(number, title)
        else:
            return self._generate_section_pages(number, title, content)
    
    def _generate_chapter_svg(self, chapter_number: str, chapter_title: str) -> List[str]:
        """生成章节页面"""
        svg_template = f'''
        <svg width="{self.config.page_width}" height="{self.config.page_height}" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="#FFFFFF"/>
            
            <!-- 章节号 -->
            <text x="{self.config.page_width/2}" y="{self.config.page_height/2 - 100}"
                  text-anchor="middle" 
                  font-family="Times New Roman, serif" 
                  font-size="{self.config.chapter_number_font_size}"
                  fill="#000000"
                  letter-spacing="2">
                {chapter_number}
            </text>
            
            <!-- 装饰线 -->
            <g transform="translate({self.config.page_width/2}, {self.config.page_height/2 - 50})">
                <line x1="-50" y1="0" x2="-15" y2="0" 
                      stroke="#000000" stroke-width="0.5"/>
                <line x1="15" y1="0" x2="50" y2="0" 
                      stroke="#000000" stroke-width="0.5"/>
                <circle cx="0" cy="0" r="1.5" fill="#000000"/>
            </g>
            
            <!-- 章节标题 -->
            <text x="{self.config.page_width/2}" y="{self.config.page_height/2 + 30}"
                  text-anchor="middle" 
                  font-family="SimSun, serif" 
                  font-size="{self.config.chapter_title_font_size}"
                  fill="#000000"
                  letter-spacing="12">
                {chapter_title}
            </text>
            
            <!-- 页码 -->
            <text x="{self.config.page_width/2}" y="{self.config.page_height - 60}"
                  text-anchor="middle"
                  font-family="Times New Roman, serif"
                  font-size="{self.config.page_number_font_size}"
                  fill="#000000">
                9
            </text>
        </svg>
        '''
        return [svg_template]
    
    def _generate_section_pages(self, section_number: str, section_title: str, content: str) -> List[str]:
        """生成小节页面（包含标题和正文）"""
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        pages = self._paginate_content(paragraphs)
        
        return [self._generate_section_page(
            section_number if i == 0 else None,
            section_title if i == 0 else None,
            page_content,
            is_first_page=(i == 0),
            page_number=i + 1
        ) for i, page_content in enumerate(pages)]
    
    def _generate_section_page(self, section_number: str, section_title: str, 
                             paragraphs: List[str], is_first_page: bool,
                             page_number: int) -> str:
        """生成小节页面"""
        svg_content = f'''
        <svg width="{self.config.page_width}" height="{self.config.page_height}" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="#FFFFFF"/>
        '''
        
        y_pos = self.config.margin_top
        
        # 仅在第一页添加标题和装饰
        if is_first_page and section_number and section_title:
            # 节序号
            svg_content += f'''
            <text x="{self.config.page_width/2}" y="{y_pos}"
                  text-anchor="middle"
                  font-family="SimSun, serif"
                  font-size="{self.config.section_number_font_size}"
                  fill="#000000">
                {section_number}
            </text>
            '''
            y_pos += 50
            
            # 装饰
            svg_content += f'''
            <g transform="translate({self.config.page_width/2}, {y_pos})">
                <line x1="-40" y1="0" x2="-15" y2="0" 
                      stroke="#000000" stroke-width="0.5"/>
                <line x1="15" y1="0" x2="40" y2="0" 
                      stroke="#000000" stroke-width="0.5"/>
                <circle cx="0" cy="0" r="1.5" fill="#000000"/>
            </g>
            '''
            y_pos += 50
            
            # 标题
            svg_content += f'''
            <text x="{self.config.page_width/2}" y="{y_pos}"
                  text-anchor="middle"
                  font-family="SimSun, serif"
                  font-size="{self.config.section_title_font_size}"
                  fill="#000000">
                {section_title}
            </text>
            '''
            y_pos += self.config.title_spacing
        
        # 正文内容
        for para in paragraphs:
            para_lines = para.split('\n')
            for line in para_lines:
                svg_content += f'''
                <text x="{self.config.margin_left}" y="{y_pos}"
                      font-family="SimSun, serif"
                      font-size="{self.config.content_font_size}"
                      fill="#000000">
                    {line}
                </text>
                '''
                y_pos += self.config.line_height
            y_pos += self.config.paragraph_spacing
        
        # 在最后添加页码
        svg_content += f'''
            <!-- 页码 -->
            <text x="{self.config.page_width/2}" y="{self.config.page_height - 60}"
                  text-anchor="middle"
                  font-family="Times New Roman, serif"
                  font-size="{self.config.page_number_font_size}"
                  fill="#000000">
                {page_number}
            </text>
        '''
        
        svg_content += '''
            </svg>
        '''
        return svg_content
    
    def _split_paragraph(self, text: str) -> List[str]:
        """改进段落分割，确保不超出右边距，且避免在标点符号处换行"""
        text = '　　' + text.strip()  # 添加首行缩进
        lines = []
        remaining = text
        first_line = True
        
        while remaining:
            # 计算当前行的最大字符数
            max_chars = self.config.chars_per_line - (2 if first_line else 0)
            
            if len(remaining) <= max_chars:
                lines.append(remaining)
                break
            
            # 寻找合适的断句点
            cut_point = max_chars
            
            # 如果当前位置是标点，向前查找非标点位置
            while cut_point > 0 and self._is_punctuation(remaining[cut_point - 1]):
                cut_point -= 1
                
            # 如果找不到合适的断句点，就使用最大长度
            if cut_point == 0:
                cut_point = max_chars
            
            # 如果切分点后面紧跟着标点，则包含这个标点
            if cut_point < len(remaining) and self._is_punctuation(remaining[cut_point]):
                cut_point += 1
            
            line = remaining[:cut_point]
            remaining = remaining[cut_point:]
            lines.append(line)
            first_line = False
        
        return lines
    
    def _is_punctuation(self, char: str) -> bool:
        """判断是否为标点符号"""
        punctuations = '，。！？；：、）》」』】'
        return char in punctuations
    
    def _paginate_content(self, paragraphs: List[str]) -> List[List[str]]:
        """优化分页逻辑，确保充分利用页面空间"""
        pages = []
        current_page = []
        
        # 计算可用高度
        first_page_height = self.config.page_height - self.config.margin_top - self.config.margin_bottom - 180  # 标题区域
        regular_page_height = self.config.page_height - self.config.margin_top - self.config.margin_bottom
        
        # 将段落拆分成行
        all_lines = []
        for para in paragraphs:
            lines = self._split_paragraph(para)
            all_lines.extend(lines)
            all_lines.append("PARAGRAPH_END")  # 标记段落结束
        
        current_height = 0
        current_para = []
        is_first_page = True
        
        for line in all_lines:
            if line == "PARAGRAPH_END":
                if current_para:
                    current_page.append('\n'.join(current_para))
                    current_para = []
                    current_height += self.config.paragraph_spacing
                continue
            
            line_height = self.config.line_height
            max_height = first_page_height if is_first_page else regular_page_height
            
            # 检查当前行是否会超出页面
            if current_height + line_height > max_height:
                # 当前页满了，创建新页面
                if current_para:
                    current_page.append('\n'.join(current_para))
                if current_page:
                    pages.append(current_page)
                
                # 重置状态
                current_page = []
                current_para = [line]
                current_height = line_height
                is_first_page = False
            else:
                # 继续添加到当前段落
                current_para.append(line)
                current_height += line_height
        
        # 处理最后的内容
        if current_para:
            current_page.append('\n'.join(current_para))
        if current_page:
            pages.append(current_page)
        
        return pages