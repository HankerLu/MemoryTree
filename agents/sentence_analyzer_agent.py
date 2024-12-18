import zhipuai
import os
from dotenv import load_dotenv

load_dotenv()

class SentenceAnalyzerAgent:
    def __init__(self):
        self.api_key = os.getenv("API_KEY_CONF")
        zhipuai.api_key = self.api_key
        
    def analyze_narrative(self, narrative_text):
        """将叙事体拆解为句子并分类"""
        prompt = f"""请将以下叙事体文本拆解为独立的句子，并为每个句子进行分类。分类包括：
1. 事实描述
2. 情感表达
3. 对话内容
4. 环境描述
5. 思考感悟

文本：
{narrative_text}

请按以下格式输出：
句子：[具体句子]
类型：[分类]
---"""
        
        try:
            response = zhipuai.ZhipuAI().chat.completions.create(
                model="chatglm_turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
            )
            
            return response.choices[0].message.content
                
        except Exception as e:
            return f"发生错误：{str(e)}"
    
    def get_sentences(self, analysis_result):
        """从分析结果中提取句子和分类"""
        sentences = []
        current_sentence = {}
        
        for line in analysis_result.split('\n'):
            line = line.strip()
            if line.startswith('句子：'):
                if current_sentence:
                    sentences.append(current_sentence.copy())
                current_sentence = {'text': line[3:]}
            elif line.startswith('类型：'):
                current_sentence['type'] = line[3:]
            elif line == '---' and current_sentence:
                sentences.append(current_sentence.copy())
                current_sentence = {}
                
        return sentences 