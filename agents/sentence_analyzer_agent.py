import zhipuai
import os
from dotenv import load_dotenv

load_dotenv()

class SentenceAnalyzerAgent:
    def __init__(self):
        self.api_key = os.getenv("API_KEY_CONF")
        zhipuai.api_key = self.api_key
        self.client = zhipuai.ZhipuAI(api_key=self.api_key)
        
    def analyze_narrative(self, narrative_text):
        """将叙事体拆解为段落并分类"""
        prompt = f"""请将以下叙事体文本按自然段落进行划分，并为每个段落进行分类。分类包括：
1. 事实描述 - 描述发生的事件和行为
2. 情感表达 - 表达情绪和感受的段落
3. 对话内容 - 包含对话或交谈的段落
4. 环境描述 - 描述场景、环境或氛围  
5. 思考感悟 - 包含个人思考、反思或感悟


文本：
{narrative_text}

请按以下格式输出：
段落：[具体段落内容]
类型：[分类]
---"""

        try:
            response = self.client.chat.completions.create(
                model="chatglm_turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
            )
            
            return response.choices[0].message.content
                
        except Exception as e:
            return f"发生错误：{str(e)}"

    def get_paragraphs(self, analysis_result):
        """从分析结果中提取段落和分类"""
        paragraphs = []
        current_paragraph = {}
        
        for line in analysis_result.split('\n'):
            line = line.strip()
            if line.startswith('段落：'):
                if current_paragraph:
                    paragraphs.append(current_paragraph.copy())
                current_paragraph = {'text': line[3:]}
            elif line.startswith('类型：'):
                current_paragraph['type'] = line[3:]
            elif line == '---' and current_paragraph:
                paragraphs.append(current_paragraph.copy())
                current_paragraph = {}
                
        return paragraphs

