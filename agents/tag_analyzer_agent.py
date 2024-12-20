import zhipuai
import os
from dotenv import load_dotenv

load_dotenv()

class TagAnalyzerAgent:
    def __init__(self):
        self.api_key = os.getenv("API_KEY_CONF")
        zhipuai.api_key = self.api_key
        self.client = zhipuai.ZhipuAI(api_key=self.api_key)
    
    def analyze_tags(self, text):
        """基于标签树分析文本中的多维度标签"""
        prompt = f"""请将以下叙事体文本按自然段落进行划分，并严格按照给定的标签体系对每个段落进行多维度标签识别。要求：

1. 时间维度：
- 人生阶段：童年(0-12岁)、青少年(13-18岁)、成年早期(18-30岁)、成年中期(30-50岁)、成年后期(50岁以后)
- 具体阶段：学前、小学、初中、高中、大学、工作初期

2. 场景维度：
- 家庭场景：亲子关系、夫妻关系、居住环境
- 学校场景：学习经历、师生关系、同学关系
- 职场场景：工作内容、职业发展、同事关系
- 社交场景：朋友关系、社团活动、兴趣爱好

3. 情感维度：
- 情感类型：快乐、悲伤、成就感、挫折
- 重要节点：转折点、人生���悟

4. 事件维度：
- 重大事件：人生选择、重要决定、意外事件、成长经历、转折点

5. 人物维度：
- 重要人物：家庭成员、恩师、朋友、同事、贵人

分析要求：
1. 只分析文本中明确提到或可以合理推断的内容
2. 不要捏造或臆测不存在的标签
3. 如果某个维度在文本中没有体现，该维度可以标注"无明确体现"
4. 以段落为单位进行分析

文本内容：
{text}

请按以下格式输出：
段落：[具体段落内容]
时间维度：[用逗号分隔的标签列表,如：小学]
场景维度：[用逗号分隔的标签列表，如：家庭,亲子关系]
情感维度：[用逗号分隔的标签列表，如：快乐]
事件维度：[用逗号分隔的标签列表，如：成长经历,转折点]
人物维度：[用逗号分隔的标签列表，如：朋友]
---"""

        try:
            response = self.client.chat.completions.create(
                model="chatglm_turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"标签分析出错：{str(e)}"
    
    def parse_tags(self, analysis_result):
        """解析分析结果，返回结构化的标签数据"""
        if not analysis_result or analysis_result.startswith("标签分析出错"):
            return []
        
        paragraphs_data = []
        current_data = {}

        
        for line in analysis_result.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('段落：'):
                if current_data:
                    paragraphs_data.append(current_data.copy())
                current_data = {
                    'text': line[3:].strip(),  # 修改这里，使用5而不是3
                    'tags': {}
                }
            
            elif line.startswith('---'):
                if current_data:
                    paragraphs_data.append(current_data.copy())
                current_data = {}
            
            elif ':' in line or '：' in line:  # 处理标签行
                for dimension in ['时间维度', '场景维度', '情感维度', '事件维度', '人物维度']:
                    if line.startswith(dimension):
                        value = line.split('：' if '：' in line else ':', 1)[1].strip()
                        if value and value != "无明确体现":
                            # 处理不同的分隔符
                            tags = [
                                tag.strip() 
                                for tag in value.replace('、', ',').split(',')
                                if tag.strip()
                            ]
                            if tags:
                                current_data['tags'][dimension] = tags
                        break
        
        # 确保最后一个段落也被添加
        if current_data:
            paragraphs_data.append(current_data.copy())
        
        return paragraphs_data