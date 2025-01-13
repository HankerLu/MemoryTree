import requests
from typing import List, Dict, Optional


class TagAnalyzerAgent:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5:1.5b"):
        """初始化标签分析器代理"""
        self.base_url = base_url
        self.model = model
        self.generation_params = {
            "temperature": 0.3  # 保持与原文件一致的低温度以获得更稳定的输出
        }

    def _call_ollama(self, prompt: str) -> Optional[str]:
        """调用Ollama API"""
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            **self.generation_params
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json().get('response')
        except requests.exceptions.RequestException as e:
            return f"标签分析出错：{str(e)}"

    def analyze_tags(self, text: str) -> str:
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
- 重要节点：转折点、人生感悟

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

        return self._call_ollama(prompt)

    def parse_tags(self, analysis_result: str) -> List[Dict]:
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
                    'text': line[3:].strip(),
                    'tags': {}
                }

            elif line.startswith('---'):
                if current_data:
                    paragraphs_data.append(current_data.copy())
                current_data = {}

            elif ':' in line or '：' in line:
                for dimension in ['时间维度', '场景维度', '情感维度', '事件维度', '人物维度']:
                    if line.startswith(dimension):
                        value = line.split('：' if '：' in line else ':', 1)[1].strip()
                        if value and value != "无明确体现":
                            tags = [
                                tag.strip()
                                for tag in value.replace('、', ',').split(',')
                                if tag.strip()
                            ]
                            if tags:
                                current_data['tags'][dimension] = tags
                        break

        if current_data:
            paragraphs_data.append(current_data.copy())

        return paragraphs_data


def main():
    # 示例使用
    agent = TagAnalyzerAgent(
        model="qwen2.5:7b"
    )
    agent.generation_params = {
        "temperature": 0.5
    }

    test_text = """我的童年，就像是一幅充满活力的画卷，而篮球场则是这幅画中最鲜艳的一抹。我记忆中的那个时代，放学后的街头，总是充满了我们的欢声笑语和篮球的“砰砰”声。

我小时候就特别喜欢打篮球，那可能是因为我长得比较高，自然而然地就被这项运动吸引。我经常和同学们组队，挑战那些看起来更加强壮的高年级选手。篮球，对我来说，不仅仅是一项运动，它是我童年最美好的回忆之一。

我记得，第一次打篮球的具体细节已经模糊，但那种兴奋和快乐的感觉至今仍清晰如初。可能是我家人的鼓励，也可能是同学们的邀请，让我开始了这段篮球之旅。在那之后，我参加了许多重要的比赛，比如市运会、新生杯和CUBA，这些比赛对我来说都是宝贵的经历。

在这些比赛中，最让我难忘的是训练的艰辛。每天训练结束后，我总是浑身散架，但那种疲惫中的成就感，让我觉得一切都是值得的。训练不仅仅是为了提升技能，更是为了培养团队精神和协作能力。

热爱，是我坚持每天进行高强度训练的动力。篮球教会了我如何面对挑战，如何在困难中寻找乐趣。教练的鼓励和队友的支持，是我不断前进的力量源泉。

篮球给我的生活带来了许多积极的变化。它让我学会了坚持和努力，这些价值观在我后来的学习和工作中都发挥了重要作用。篮球也影响了我的其他人生选择，让我更加注重团队合作和个人成长。

每当我回想起那些在篮球场上的日子，心中总是充满了温暖和感激。篮球，它不仅仅是一项运动，它是我的青春，是我的梦想，是我人生中不可或缺的一部分。"""

    # 分析标签
    analysis_result = agent.analyze_tags(test_text)
    print("原始分析结果：")
    print(analysis_result)
    print("\n解析后的结构化数据：")
    parsed_results = agent.parse_tags(analysis_result)
    for result in parsed_results:
        print(result)


if __name__ == "__main__":
    main()