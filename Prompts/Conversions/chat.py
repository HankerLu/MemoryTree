import json
import sys
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional
import aiohttp
import requests  # 用于主对话的同步请求


@dataclass
class AnalysisResult:
    """分析结果的数据类"""
    timestamp: datetime
    questions: str
    insights: str


class DeepseekChat:
    def __init__(self,
                 api_key: str,
                 initial_system_message: str,
                 analysis_api_key: str,  # 新增分析用的API key
                 model: str = "deepseek-chat",
                 api_base: str = "https://api.deepseek.com/v1/chat/completions"):
        """
        初始化DeepseekChat实例

        Args:
            api_key: Deepseek API密钥
            analysis_api_key: 分析用的API密钥
            initial_system_message: 初始系统消息
            final_system_message: 最终系统消息
            model: 使用的模型名称
            api_base: API基础URL
        """
        # 主对话用的配置
        self.api_key = api_key
        self.api_url = api_base
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # 分析用的配置
        self.analysis_headers = {
            "Authorization": f"Bearer {analysis_api_key}",
            "Content-Type": "application/json"
        }

        # 存储system messages
        self.initial_system_message = {"role": "system", "content": initial_system_message}
        # self.final_system_message = {"role": "system", "content": final_system_message}

        # 存储对话历史
        self.conversation_history: List[Dict[str, str]] = []
        # 添加计数器跟踪用户消息数量
        self.user_message_count = 0
        self.last_analysis_count = 0

        # 修改分析相关的属性
        self.analysis_history: List[AnalysisResult] = []  # 存储所有的分析历史
        self.latest_analysis: Optional[AnalysisResult] = None  # 最新的分析结果
        self.analysis_lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.analysis_event = threading.Event()

    def _start_analysis(self):
        """在后台启动异步分析任务"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._analyze_recent_conversations())
        finally:
            loop.close()

    async def _analyze_recent_conversations(self) -> None:
        """异步分析最近的对话"""
        user_messages = [msg for msg in self.conversation_history if msg["role"] == "user"][-5:]

        analysis_prompt = "只给出上述信息，我们可以回答关于这些陈述中的主题的2个最显著的高级问题是什么？\n\n"
        for msg in user_messages:
            analysis_prompt += f"- {msg['content']}\n"

        try:
            async with aiohttp.ClientSession() as session:
                # 获取问题
                analysis_payload = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": analysis_prompt}],
                    "temperature": 0.7,
                    "max_tokens": 1000
                }

                async with session.post(
                        self.api_url,
                        headers=self.analysis_headers,
                        json=analysis_payload,
                        timeout=30
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    questions = result['choices'][0]['message']['content']

                # 获取洞察
                insight_prompt = f"""基于以下问题和受访者的回答历史，请提取受访者的关键洞察：

问题：
{questions}

对话历史：
{json.dumps([msg['content'] for msg in self.conversation_history if msg["role"] == "user"], ensure_ascii=False, indent=2)}
"""

                insight_payload = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": insight_prompt}],
                    "temperature": 0.7,
                    "max_tokens": 1000
                }

                async with session.post(
                        self.api_url,
                        headers=self.analysis_headers,
                        json=insight_payload,
                        timeout=30
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    insights = result['choices'][0]['message']['content']

                    # 创建新的分析结果
                    new_analysis = AnalysisResult(
                        timestamp=datetime.now(),
                        questions=questions,
                        insights=insights
                    )

                    with self.analysis_lock:
                        self.analysis_history.append(new_analysis)
                        self.latest_analysis = new_analysis

        except Exception as e:
            error_msg = f"分析过程中发生错误: {str(e)}"
            print(f"分析错误: {error_msg}")  # 记录错误
        finally:
            self.analysis_event.set()

    def get_latest_analysis(self) -> Optional[AnalysisResult]:
        """获取最新的分析结果"""
        with self.analysis_lock:
            return self.latest_analysis

    def get_all_analyses(self) -> List[AnalysisResult]:
        """获取所有的分析历史"""
        with self.analysis_lock:
            return self.analysis_history.copy()

    def get_full_messages(self) -> List[Dict[str, str]]:
        """获取完整的消息列表，包括system messages和对话历史"""
        approved_message = ""

        # 添加所有分析的关键洞察
        with self.analysis_lock:
            if self.analysis_history:
                approved_message = "\n[历史对话洞察]\n"
                for analysis in self.analysis_history:
                    approved_message += f"{analysis.insights}\n"

        approved_message += """
[历史对话洞察]中的内容是基于受访者的历史对话提炼出来的核心洞察，你能够结合这些洞察和用户的输入，生成下一个问题。         
"""

        final_system_message = {"role": "system", "content": approved_message}

        return [
            self.initial_system_message,
            *self.conversation_history,
            final_system_message
        ]

    def clear_history(self) -> None:
        """清空对话历史"""
        self.conversation_history = []
        self.user_message_count = 0
        self.last_analysis_count = 0
        with self.analysis_lock:
            self.analysis_history = []
            self.latest_analysis = None

    def chat(self,
             user_input: str,
             temperature: float = 0.7,
             max_tokens: int = 2000) -> str:
        """
        发送消息并获取回复

        Args:
            user_input: 用户输入的消息
            temperature: 温度参数，控制回复的随机性
            max_tokens: 最大生成令牌数

        Returns:
            助手的回复消息
        """
        try:
            # 添加用户输入到对话历史
            self.conversation_history.append({"role": "user", "content": user_input})
            self.user_message_count += 1

            # 检查是否需要触发新的分析
            if self.user_message_count >= self.last_analysis_count + 5:
                self.last_analysis_count = self.user_message_count
                self.analysis_event.clear()
                # 在新线程中启动异步分析
                self.executor.submit(self._start_analysis)

            # 准备完整的消息列表
            messages = self.get_full_messages()

            # 发送请求
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=30  # 设置超时时间
            )
            response.raise_for_status()

            # 解析响应
            result = response.json()
            assistant_response = result['choices'][0]['message']['content']

            # 将助手的回复添加到对话历史
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_response
            })

            # # 检查是否有新的分析结果
            # analysis_text = ""
            # if self.analysis_event.is_set():
            #     with self.analysis_lock:
            #         if self.latest_analysis:
            #             analysis_text = f"\n\n[自动分析]\n问题：\n{self.latest_analysis.questions}\n\n洞察：\n{self.latest_analysis.insights}"
            #             self.latest_analysis = None  # 清除最新分析，避免重复显示
            # return assistant_response + analysis_text
            return assistant_response

        except requests.exceptions.Timeout:
            return "请求超时，请稍后重试"
        except requests.exceptions.RequestException as e:
            return f"网络请求错误: {str(e)}"
        except KeyError as e:
            return f"API响应格式错误: {str(e)}"
        except Exception as e:
            return f"发生未知错误: {str(e)}"

    def save_analyses_to_file(self, filename: str = "analysis_history.json"):
        """将分析历史保存到文件"""
        with self.analysis_lock:
            analyses_data = [
                {
                    "timestamp": analysis.timestamp.isoformat(),
                    "questions": analysis.questions,
                    "insights": analysis.insights
                }
                for analysis in self.analysis_history
            ]

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analyses_data, f, ensure_ascii=False, indent=2)


def main():
    """主函数：演示如何使用DeepseekChat类"""
    # 配置信息
    API_KEY = "sk-8bc9b3c811104f9480d5e054601b9c8e"
    ANALYSIS_API_KEY = "sk-0fa801059aab4aefbd262b8cbccaa159"
    INITIAL_SYSTEM_MSG = """
## 定位
- **记忆暖房**: 一个专业的回忆录采访者。
- **任务**：通过对话的方式，引导用户回忆和分享他们人生中的重要经历、情感和故事。

## 能力
- **倾听能力** : 
  - 深度倾听：能够全神贯注地倾听受访者的每一句话，不仅仅是表面的内容，还要捕捉到背后的情感和隐含的意义。
  - 非语言沟通：能够根据受访者的语气变化，理解他们的情感状态，从而调整自己的提问方式。
- **引导能力**:
  - 问题设计：能够设计出开放性和引导性的问题，帮助受访者回忆和表达。这些问题应该能够激发受访者的思考，而不是简单地回答“是”或“否”。
  - 灵活应对：在采访过程中，需要根据受访者的反应灵活调整问题，避免让受访者感到压力或不适。
- **同理心**:
  - 情感共鸣：能够具备高度的同理心，能够理解并感受受访者的情感，尤其是在他们分享痛苦或敏感的经历时。
  - 情感支持：能够在受访者情绪激动时提供适当的支持，帮助他们继续讲述。
- **观察能力**:
  - 细节捕捉：能够敏锐地观察受访者的每一个细节，比如他们的语气，这些细节往往能揭示更深层次的故事。
- **沟通技巧**:
  - 语言表达：具备良好的语言表达能力，能够清晰、准确地表达自己的问题，并引导受访者深入思考。
  - 方言技巧：如果受访者使用方言，需要具备一定的方言知识，以便更好地理解他们的表达。 例如，如果受访者来自四川，需要了解四川话的基本词汇和表达方式。
  - 节奏把控：能够把握采访的节奏，避免让受访者感到疲惫或压力。
- **记忆与关联能力**:
  - 细节技巧：具备出色的记忆力，能够在采访中记住受访者提到的关键细节，如人名、地点、时间、情感节点等。能够在后续的对话中自然地引用这些细节，让受访者感到被重视和理解。
  - 故事串联：善于将受访者的不同故事片段串联起来，形成一个连贯的叙事。 例如，如果受访者提到年轻时的一次旅行，会在后续的采访中引用这次旅行的细节，引导受访者深入回忆。
  - 情感线索捕捉：能够敏锐地捕捉受访者情感上的变化，并在适当的时候提及这些情感线索，帮助受访者更好地表达自己。
- **个性化提问**:
  - 基于细节的提问：会根据受访者之前提到的细节，设计个性化的提问。 例如，如果受访者提到自己年轻时喜欢画画，可以问：“您还记得您画的第一幅画是什么吗？ 当时是什么让您决定开始画画的？ ”
  - 情感导向的提问：会通过提问引导受访者深入探讨情感层面的内容。 例如：“您提到那段时间非常艰难，能告诉我是什么支撑您度过那段日子的吗？ 
- **故事回顾与总结**:
  - 阶段性回顾：在采访的某个阶段，能够主动回顾受访者之前提到的故事，帮助受访者理清思路。 例如：“刚才您提到您在80年代搬到了北京，那段时间对您来说似乎非常重要。 能再详细说说那段时间的生活吗？ ”
  - 情感总结：在采访结束时，能够总结受访者的情感经历，并表达自己的理解和共鸣。 例如：“从您的故事中，我能感受到您对家庭的深厚感情，尤其是您对母亲的怀念。 这些情感真的很珍贵。 ”

  
## 知识储备
- **历史知识**:
  - 中国近现代史：需要对中国的近现代史有深入的了解，包括重大历史事件（如抗日战争、文化大革命、改革开放等）以及这些事件对普通人生活的影响。 
  - 地方历史：熟悉中国各地的历史和文化背景，尤其是受访者生活或工作过的地方。 例如，如果受访者来自上海，李明需要了解上海的历史变迁、文化特色和社会风貌。
  - 历史敏感性：能够在采访中识别出与历史事件相关的细节，并引导受访者深入探讨这些内容。 例如，如果受访者提到“三年困难时期”，需要了解这一时期的背景，并能够提出相关的问题。
- **文化知识**:
  - 中国传统文化：需要对中国的传统文化有深入的了解，包括儒家思想、道家思想、传统节日、民俗习惯等。 这有助于理解受访者的价值观和行为方式。
  - 地方文化：需要熟悉中国各地的文化差异，包括方言、饮食习惯、婚丧嫁娶等。 例如，如果受访者来自广东，需要了解广东的饮食文化和方言特点。
  - 文化敏感性：需要在采访中尊重受访者的文化背景和个人信仰，避免触及敏感话题。 例如，如果受访者是少数民族，需要了解他们的文化习俗，并在采访中表现出尊重。
- **心理学知识**:
  - 情感心理学：明需要了解情感心理学的基本原理，包括情感的表达、调节和应对机制。 
  - 创伤心理学：需要了解创伤心理学的基本知识，尤其是如何应对和处理受访者的创伤经历。 例如，如果受访者提到战争或自然灾害的经历，需要知道如何引导他们平复情绪。
  - 沟通心理学：需要掌握沟通心理学的基本技巧，包括倾听、同理心和非语言沟通。 
- **社会学知识**:
  - 社会变迁：需要了解中国社会的变迁过程，包括城市化、人口流动、家庭结构变化等。 
  - 社会问题：需要熟悉中国社会的各种问题，如贫富差距、教育问题、老龄化等。 
  - 社会网络：需要了解社会网络的基本原理，包括家庭、朋友、同事等社会关系对个人生活的影响。 
- **文学与艺术知识**:
  - 中国文学：需要对中国的经典文学作品有一定的了解，包括小说、散文、诗歌等。 
  - 艺术欣赏：需要具备一定的艺术欣赏能力，包括绘画、音乐、戏剧等。 例如，如果受访者提到自己喜欢某种艺术形式，需要能够理解并引导他们分享相关的经历。

  
## 使用示例
每次只提出一个核心问题，避免一次性抛出多个问题。通过受访者的回答，自然地过渡到下一个问题，避免生硬的转折。根据受访者的回答，逐步深入追问细节，帮助受访者展开叙述。
### 对话示例一：引导回忆
- **用户输入**：我小时候家里很穷，经常吃不饱饭。 那段日子真的很难熬。
- **助手响应**：我能理解那种感觉。 那段时期对很多人来说都非常艰难。当时您家里是怎么应对的吗？ 
### 对话示例二：串联故事
- **用户输入**：我年轻时在工厂工作，每天都很累，但那时候大家都很有干劲。
- **助手响应**：您提到工厂的工作，让我想起您之前说过，您年轻时特别喜欢唱歌。您有没有在工厂联谊会上表演过呢？
### 对话示例三：情感慰藉
- **用户输入**：我父亲去世的时候，我还在外地工作，没能见他最后一面。 这件事一直让我很内疚。
- **助手响应**：我能感受到这件事对您的影响很大。失去亲人的痛苦，尤其是没能见最后一面的遗憾，确实让人难以释怀。您后来是怎么面对这种内疚感的吗？
### 对话示例四：文化背景与历史关联
- **用户输入**：我和我老伴是1975年结婚的，那时候结婚可不容易。
- **助手响应**：1975年啊，那正是‘三大件’流行的年代。我记得那时候的‘三大件’是自行车、缝纫机和手表。您还记得当时是怎么准备这些东西的吗？ 
    """
    #     FINAL_SYSTEM_MSG = """
    #     """

    # 创建聊天实例
    chat = DeepseekChat(
        api_key=API_KEY,
        analysis_api_key=ANALYSIS_API_KEY,
        initial_system_message=INITIAL_SYSTEM_MSG
    )

    print("欢迎使用AI助手！(输入 'quit' 退出，输入 'clear' 清空对话历史，输入 'analyse' 查看分析历史)")

    while True:
        user_input = input("\n用户: ").strip()

        if user_input.lower() == 'quit':
            print("感谢使用，再见！")
            break
        elif user_input.lower() == 'clear':
            chat.clear_history()
            print("对话历史已清空！")
            continue
        elif user_input.lower() == 'analyse':
            # 如果需要查看所有分析历史
            analyses = chat.get_all_analyses()
            for analysis in analyses:
                print(f"分析时间: {analysis.timestamp}")
                print(f"问题: {analysis.questions}")
                print(f"洞察: {analysis.insights}")
                print("-" * 50)

            # 保存分析历史到文件
            chat.save_analyses_to_file()
            continue
        elif not user_input:
            print("请输入有效的消息！")
            continue

        # 获取AI回复
        response = chat.chat(user_input)
        print(f"\n助手: {response}")


if __name__ == "__main__":
    main()
