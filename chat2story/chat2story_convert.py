import os
import zhipuai
from dotenv import load_dotenv
import re

class Chat2Story:
    def __init__(self):
        # 加载环境变量
        load_dotenv()
        self.api_key = os.getenv("API_KEY_CONF")
        if not self.api_key:
            raise ValueError("未找到API密钥，请检查环境变量 API_KEY_CONF")
        self.client = zhipuai.ZhipuAI(api_key=self.api_key)
        
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
"1980年的盛夏，我怀着憧憬来到这座城市。那���我刚从大学毕业，年轻气盛，对未来充满期待。记得那天骄阳似火，但丝毫没有影响我激动的心情。"

请开始转换工作。"""

    def read_interview(self, filename='interview_record.md'):
        """读取访谈记录文件"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"读取文件时发生错误：{str(e)}")
            return None

    def split_text(self, text, max_length=1000):
        """将长文本分段"""
        # 按照说话者分割
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
            
        return segments_result

    def convert_segment(self, segment):
        """转换单个文本段落"""
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"请将以下访谈内容转换为优美的第一人称叙事文本：\n\n{segment}"}
            ]
            
            response = self.client.chat.completions.create(
                model="glm-4",
                messages=messages,
                temperature=0.7,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"转换段落时发生错误：{str(e)}")
            return None

    def convert(self, input_file='interview_record.md', output_file='output.md'):
        """执行完整的转换流程"""
        # 读取访谈文本
        interview_text = self.read_interview(input_file)
        if not interview_text:
            return False
            
        # 分段处理
        segments = self.split_text(interview_text)
        
        # 转换每个段落
        converted_segments = []
        for segment in segments:
            converted_text = self.convert_segment(segment)
            if converted_text:
                converted_segments.append(converted_text)
            
        # 合并并保存结果
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# 回忆录\n\n")
                f.write("\n\n".join(converted_segments))
            return True
        except Exception as e:
            print(f"保存文件时发生错误：{str(e)}")
            return False

def main():
    converter = Chat2Story()
    success = converter.convert()
    if success:
        print("转换完成！")
    else:
        print("转换过程中发生错误。")

if __name__ == "__main__":
    main()
