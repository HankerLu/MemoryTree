import zhipuai
import os
from dotenv import load_dotenv

load_dotenv()

class SentenceAnalyzerAgent:
    def __init__(self):
        self.api_key = os.getenv("e64b996267bee6ba0252a5d46a143ff4.3RZ8v4qZ2DbYoJbk")
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
            response = zhipuai.model_api.invoke(
                model="chatglm_turbo",
                prompt=[{"role": "user", "content": prompt}],
                temperature=0.5,
            )
            
            if response.get("code") == 200:
                return response["data"]["choices"][0]["content"]
            else:
                return f"错误：{response.get('msg', '未知错误')}"
                
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