import asyncio
import json
from typing import List, Dict
import aiohttp


class TestAnalysis:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.model = "deepseek-chat"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # 模拟的对话历史
        self.conversation_history: List[Dict[str, str]] = [
            {"role": "user", "content": "我小时候家里很穷，经常吃不饱饭。那段日子真的很难熬。"},
            {"role": "assistant",
             "content": "听到您说这些，我能感受到那段时期的艰辛。您愿意跟我说说当时家里是怎么度过那段困难时期的吗？"},
            {"role": "user", "content": "那时候我妈经常煮稀饭，放一点咸菜。有时候能买到一点红薯，就觉得特别开心。"},
            {"role": "assistant",
             "content": "这些记忆一定给您留下了深刻的印象。能分享一下那时候最让您记忆深刻的一顿饭是什么吗？"},
            {"role": "user", "content": "记得有一年过年，邻居家分了我们一些饺子，那可能是我吃过最香的饺子。"},
            {"role": "assistant",
             "content": "这个回忆很温暖。邻里之间的互帮互助确实特别珍贵。您还记得那时候邻居们之间的关系是怎样的吗？"},
            {"role": "user", "content": "那时候邻居关系特别好，大家都互相帮助。"},
            {"role": "assistant",
             "content": "这种守望相助的情谊确实很难得。您觉得现在的邻里关系和那时候比，有什么变化吗？"},
            {"role": "user", "content": "现在大家都很忙，很少有时间串门聊天了。但我还是会经常想起以前的日子。"}
        ]

    async def analyze_recent_conversations(self) -> str:
        """分析最近的对话"""
        # 获取最近的5条用户消息
        user_messages = [msg for msg in self.conversation_history if msg["role"] == "user"][-5:]

        # 构建分析提示
        analysis_prompt = "只给出上述信息，我们可以回答关于这些陈述中的主题的2个最显著的高级问题是什么？\n\n"
        for msg in user_messages:
            analysis_prompt += f"- {msg['content']}\n"

        try:
            async with aiohttp.ClientSession() as session:
                # 发送分析请求获取问题
                analysis_payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": analysis_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000
                }

                print("\n[发送问题生成请求...]")
                print(f"提示词：\n{analysis_prompt}")

                async with session.post(
                        self.api_url,
                        headers=self.headers,
                        json=analysis_payload,
                        timeout=30
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    questions = result['choices'][0]['message']['content']

                print(f"\n[生成的问题：]\n{questions}")

                # 使用生成的问题分析整个对话历史
                insight_prompt = f"""基于以下问题和完整的用户回答，请提取用户的最关键的两个洞察：

问题：
{questions}

对话历史：
{json.dumps([msg['content'] for msg in self.conversation_history if msg["role"] == "user"], ensure_ascii=False, indent=2)}
"""

                insight_payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": insight_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000
                }

                print("\n[发送洞察分析请求...]")

                async with session.post(
                        self.api_url,
                        headers=self.headers,
                        json=insight_payload,
                        timeout=30
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    insights = result['choices'][0]['message']['content']

                print(f"\n[生成的洞察：]\n{insights}")
                return insights

        except Exception as e:
            error_msg = f"分析过程中发生错误: {str(e)}"
            print(f"\n[错误]\n{error_msg}")
            return error_msg


async def main():
    # 替换为您的 API key
    api_key = "sk-8bc9b3c811104f9480d5e054601b9c8e"

    analyzer = TestAnalysis(api_key)
    result = await analyzer.analyze_recent_conversations()

    print("\n[完整分析结果]")
    print("-" * 50)
    print(result)
    print("-" * 50)


if __name__ == "__main__":
    asyncio.run(main())