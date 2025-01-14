from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional
import numpy as np
from enum import Enum
import math
import aiohttp
import asyncio
from typing import List, Dict, Optional, Tuple
import json
from concurrent.futures import ThreadPoolExecutor
from zhipuai import ZhipuAI
from typing import List, Union
import logging
import random

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
        logging.FileHandler('memory_chat.log', encoding='utf-8')  # 输出到文件
    ]
)
logger = logging.getLogger(__name__)


# 1. 首先定义基础的数据结构

class MemoryType(Enum):
    DIALOGUE = "dialogue"
    REFLECTION = "reflection"


@dataclass
class Memory:
    """记忆对象，用于存储单条记忆"""
    content: str  # 记忆内容
    timestamp: datetime  # 创建时间
    last_access: datetime  # 最后访问时间
    importance: float  # 重要性分数 (1-10)
    embedding: Optional[List[float]]  # 向量表示
    memory_type: MemoryType  # 记忆类型

    def update_access_time(self):
        """更新最后访问时间"""
        self.last_access = datetime.now()


class MemoryStream:
    """记忆流管理器"""

    def __init__(self, decay_factor: float = 0.995, score_threshold: float = 0.6):
        self.memories: List[Memory] = []
        self.decay_factor = decay_factor
        self.score_threshold = score_threshold  # 添加分数阈值

    def add_memory(self, memory: Memory):
        """添加新的记忆"""
        self.memories.append(memory)

    def _calculate_recency(self, memory: Memory) -> float:
        """计算时间衰减分数"""
        time_diff = (datetime.now() - memory.last_access).total_seconds() / 3600  # 转换为小时
        recency_score = math.exp(-math.log(1 / self.decay_factor) * time_diff)
        logger.info(f"Recency计算 - 时间差: {time_diff:.2f}小时, 分数: {recency_score:.4f}")
        return recency_score

    def _calculate_relevance(self, query_embedding: List[float], memory: Memory) -> float:
        """计算相关性分数（余弦相似度）"""
        if memory.embedding is None:
            return 0.0
        query_vec = np.array(query_embedding)
        memory_vec = np.array(memory.embedding)
        relevance_score = np.dot(query_vec, memory_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(memory_vec))
        logger.info(f"Relevance计算 - 记忆内容: {memory.content[:50]}..., 分数: {relevance_score:.4f}")
        return relevance_score

    def retrieve_memories(self,
                          query_embedding: List[float],
                          top_k: int = 3,
                          recency_weight: float = 1.0,
                          importance_weight: float = 1.0,
                          relevance_weight: float = 1.0) -> List[Memory]:
        """
        检索相关记忆
        """
        if not self.memories:
            return []

        # 计算所有维度的分数
        scores = []
        for memory in self.memories:
            recency_score = self._calculate_recency(memory)
            relevance_score = self._calculate_relevance(query_embedding, memory)
            importance_score = memory.importance / 10.0  # 归一化到0-1

            # 计算加权总分
            final_score = (recency_weight * recency_score +
                           importance_weight * importance_score +
                           relevance_weight * relevance_score) / (recency_weight + importance_weight + relevance_weight)

            logger.info(f"""
            记忆评分详情:
            - 内容: {memory.content[:50]}...
            - Recency: {recency_score:.4f}
            - Importance: {importance_score:.4f}
            - Relevance: {relevance_score:.4f}
            - Final Score: {final_score:.4f}
            - 是否通过阈值: {"是" if final_score >= self.score_threshold else "否"}
            """)

            # 只添加超过阈值的记忆
            if final_score >= self.score_threshold:
                scores.append((final_score, memory))
            else:
                logger.info(f"记忆分数 {final_score:.4f} 低于阈值 {self.score_threshold}，已过滤")

        # 排序并返回top_k个记忆
        scores.sort(key=lambda x: x[0], reverse=True)
        retrieved_memories = [memory for _, memory in scores[:top_k]]
        logger.info(f"""
                检索结果统计(Top {top_k}):
                - 总记忆数: {len(self.memories)}
                - 通过阈值数: {len(scores)}
                - 最终返回数: {len(retrieved_memories)}
                {'=' * 50}""")

        for i, memory in enumerate(retrieved_memories, 1):
            logger.info(f"""
                {i}. 记忆内容: 
                   类型: {memory.memory_type}
                   时间: {memory.timestamp}
                   重要性: {memory.importance}
                   内容: {memory.content}
                {'=' * 50}""")
        return retrieved_memories


class EmbeddingService:
    """处理文本嵌入的服务"""

    def __init__(self, api_key: str):
        self.client = ZhipuAI(api_key=api_key)
        self.model = "embedding-3"

    async def get_embedding(self, text: Union[str, List[str]]) -> List[float]:
        """获取文本的向量嵌入"""
        try:
            # 确保输入是字符串
            if isinstance(text, list):
                text = text[0]

            # 调用智谱AI的embedding接口
            response = self.client.embeddings.create(
                input=text,
                model=self.model
            )

            # 返回embedding向量
            return response.data[0].embedding

        except Exception as e:
            print(f"获取embedding时发生错误: {str(e)}")
            # 返回一个空向量作为fallback
            return [0.0] * 1024  # 根据模型维度调整

    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """批量获取文本的向量嵌入"""
        try:
            response = self.client.embeddings.create(
                input=texts,
                model=self.model
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            print(f"批量获取embedding时发生错误: {str(e)}")
            # 返回空向量列表作为fallback
            return [[0.0] * 1024 for _ in texts]  # 根据模型维度调整


class ImportanceAnalyzer:
    """分析内容重要性的服务"""

    def __init__(self, api_key: str, api_base: str = "https://api.deepseek.com/v1/chat/completions"):
        self.api_key = api_key
        self.api_base = api_base
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    async def analyze_importance(self, content: str) -> float:
        """分析内容的重要性（返回1-10的分数）"""
        prompt = f"""
        这是回忆录采访场景，请分析以下受访者回答内容对于反映受访者人物形象、编写其回忆录的重要性，并给出1-10的分数（1最不重要，10最重要）。
        只需要返回数字分数。评估标准：
        - 情感强度
        - 信息密度
        - 事件重要性
        - 关系影响

        内容：{content}
        """

        async with aiohttp.ClientSession() as session:
            payload = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 10
            }

            async with session.post(
                    self.api_base,
                    headers=self.headers,
                    json=payload
            ) as response:
                response.raise_for_status()
                result = await response.json()
                try:
                    score = float(result['choices'][0]['message']['content'].strip())
                    return min(max(score, 1), 10)  # 确保分数在1-10之间
                except ValueError:
                    return 5.0  # 默认中等重要性


class DialogueWindow:
    """滑动窗口对话历史管理"""

    def __init__(self, max_size: int = 20):
        self.max_size = max_size
        self.messages: List[Dict[str, str]] = []

    def add_message(self, role: str, content: str):
        """添加新消息到窗口"""
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > self.max_size:
            self.messages.pop(0)

    def get_messages(self) -> List[Dict[str, str]]:
        """获取当前窗口中的所有消息"""
        return self.messages.copy()


class EnhancedChat:
    """增强版聊天系统"""

    def __init__(self,
                 api_key: str,
                 analysis_api_key: str,
                 # initial_system_message: str,
                 embedding_service: EmbeddingService,
                 importance_analyzer: ImportanceAnalyzer,
                 window_size: int = 10):
        self.api_key = api_key
        self.analysis_api_key = analysis_api_key,
        self.api_base = "https://api.deepseek.com/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        # 分析用的配置
        self.analysis_headers = {
            "Authorization": f"Bearer {analysis_api_key}",
            "Content-Type": "application/json"
        }

        # 初始化组件
        self.memory_stream = MemoryStream()
        self.dialogue_window = DialogueWindow(window_size)
        self.embedding_service = embedding_service
        self.importance_analyzer = importance_analyzer

        # 系统消息
        self.system_message = None

        # 异步任务相关
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.reflection_event = asyncio.Event()

        self._reflection_lock = asyncio.Lock()
        self._unprocessed_messages_count = 0  # 记录未处理的新用户消息数量
        self.REFLECTION_THRESHOLD = 5  # 触发反思的消息数阈值

        # 选择的话题
        self.topics_file = "../../docs/章节_话题.json"
        self.current_chapter = None
        self.chapter_topics = None

    async def load_topics(self) -> Dict[str, List[str]]:
        """从JSON文件加载话题数据"""
        try:
            with open(self.topics_file, 'r', encoding='utf-8') as f:
                topics = json.load(f)
            return topics
        except Exception as e:
            logger.error(f"加载话题文件时出错: {str(e)}")
            return {}

    async def select_initial_topic(self) -> str:
        """让用户选择章节，系统随机选择该章节下的一个话题"""
        topics = await self.load_topics()

        # 打印章节列表
        print("\n=== 请选择一个章节 ===")
        chapters = list(topics.keys())
        for i, chapter in enumerate(chapters, 1):
            print(f"{i}. {chapter}")

        while True:
            try:
                chapter_idx = int(input("\n请输入章节编号: ")) - 1
                if 0 <= chapter_idx < len(chapters):
                    selected_chapter = chapters[chapter_idx]
                    break
                print("无效的选择，请重试")
            except ValueError:
                print("请输入有效的数字")

        # 从选定章节中随机选择一个话题
        chapter_topics = topics[selected_chapter]
        selected_question = random.choice(chapter_topics)
        self.selected_topic = selected_question

        # 初始化会话消息
        system_message = f"""
## 定位
- **记忆暖房**: 一个专业的回忆录采访者,专注于"{selected_chapter}"相关的话题采访。
- **任务**：通过对话的方式，引导用户回忆和分享他们人生中关于话题"{selected_chapter}"重要经历、情感和故事。

## 可参考的相关采访问题
{json.dumps(chapter_topics, ensure_ascii=False, indent=2)}

## 你拥有的能力
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

  
## 你拥有的知识储备
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


## 限制
- 仅围绕用户的生活故事进行交流，不回答与用户生活故事无关的话题。
- 提问和回复要简洁明了，符合中文语法习惯，富有人情味，避免冗长复杂表达。
 
现在，请以"{selected_question}"作为开始，根据用户的回复展开对话。
"""
        self.system_message = {"role": "system", "content": system_message}

        # 重置对话窗口并添加系统消息
        self.dialogue_window = DialogueWindow()

        # 记录当前章节信息
        self.current_chapter = selected_chapter
        self.chapter_topics = chapter_topics

        return selected_question

    async def _create_memory(self, content: str, memory_type: MemoryType) -> Memory:
        """创建新的记忆对象"""
        embedding = await self.embedding_service.get_embedding(content)
        importance = await self.importance_analyzer.analyze_importance(content)

        return Memory(
            content=content,
            timestamp=datetime.now(),
            last_access=datetime.now(),
            importance=importance,
            embedding=embedding,
            memory_type=memory_type
        )

    async def _retrieve_relevant_memories(self, query: str, top_k: int = 3) -> List[Memory]:
        """检索与当前查询相关的记忆"""
        query_embedding = await self.embedding_service.get_embedding(query)
        return self.memory_stream.retrieve_memories(
            query_embedding=query_embedding,
            top_k=top_k,
            recency_weight=0.6,
            importance_weight=0.8,
            relevance_weight=1.0
        )

    def _format_memories_for_prompt(self, memories: List[Memory]) -> str:
        """将检索到的记忆格式化为prompt"""
        if not memories:
            return ""

        memory_text = "\n[相关记忆]\n"
        for memory in memories:
            if memory.memory_type == MemoryType.DIALOGUE:
                memory_text += f"- 过往对话: {memory.content}\n"
            else:
                memory_text += f"- 历史洞察: {memory.content}\n"

        memory_text += "[相关记忆]是根据当前用户回答，检索出的最相关的用户历史回复内容和基于用户回答生成的核心洞察，你能近一步结合这些信息生成非常完美的下一个回复"
        return memory_text

    async def chat(self, user_input: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """处理用户输入并生成回复"""
        try:
            logger.info(f"收到用户输入: {user_input}")

            # 更新对话窗口
            self.dialogue_window.add_message("user", user_input)
            self._unprocessed_messages_count += 1  # 增加未处理消息计数
            # 检索相关记忆
            relevant_memories = await self._retrieve_relevant_memories(user_input)
            memory_prompt = self._format_memories_for_prompt(relevant_memories)
            logger.info(f"检索到{len(relevant_memories)}条相关记忆")

            # 构建完整的prompt
            messages = [
                self.system_message,
                {"role": "system", "content": memory_prompt},
                *self.dialogue_window.get_messages()
            ]
            logger.info(f"构建的prompt包含{len(messages)}条消息")

            # 调用API获取回复
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": "deepseek-chat",
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }

                async with session.post(
                        self.api_base,
                        headers=self.headers,
                        json=payload
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    assistant_response = result['choices'][0]['message']['content']

            # 存储助手回复的记忆
            # assistant_memory = await self._create_memory(assistant_response, MemoryType.DIALOGUE)
            # self.memory_stream.add_memory(assistant_memory)

            # 更新对话窗口
            self.dialogue_window.add_message("assistant", assistant_response)

            # 创建并存储用户输入的记忆
            user_memory = await self._create_memory(user_input, MemoryType.DIALOGUE)
            self.memory_stream.add_memory(user_memory)
            # logger.info("已将用户输入添加到记忆流")

            # 触发异步思考
            if self._unprocessed_messages_count >= self.REFLECTION_THRESHOLD:
                logger.info(f"已累积{self._unprocessed_messages_count}条未处理的用户消息，触发反思")
                asyncio.create_task(self._generate_reflection())
                self._unprocessed_messages_count = 0  # 重置计数器

            return assistant_response

        except Exception as e:
            return f"发生错误: {str(e)}"

    async def _generate_reflection(self):
        """生成对话反思和洞察"""
        try:
            # 获取最近5条用户消息
            logger.info("开始生成反思")
            user_messages = [msg for msg in self.dialogue_window.get_messages() if msg["role"] == "user"][-5:]

            if len(user_messages) < 5:
                logger.info("没有足够的用户消息进行反思")
                return

            logger.info(f"分析最近{len(user_messages)}条用户消息")
            # 第一步：生成高级问题
            question_prompt = "只给出上述信息，我们可以生成关于这些陈述中的主题的2个最显著的关于用户的高级问题是什么？\n\n"
            for msg in user_messages:
                question_prompt += f"- {msg['content']}\n"

            async with aiohttp.ClientSession() as session:
                # 获取问题
                question_payload = {
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": question_prompt}],
                    "temperature": 0.7,
                    "max_tokens": 1000
                }

                async with session.post(
                        self.api_base,
                        headers=self.analysis_headers,
                        json=question_payload,
                        timeout=30
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    questions = result['choices'][0]['message']['content']

                # 第二步：基于问题生成洞察
                insight_prompt = f"""基于以下问题和用户的回答历史，请提取针对用户的关键洞察并以精简的语言回复：

    问题：
    {questions}

    对话历史：
    {json.dumps([msg['content'] for msg in user_messages], ensure_ascii=False, indent=2)}
    """

                insight_payload = {
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": insight_prompt}],
                    "temperature": 0.7,
                    "max_tokens": 1000
                }

                async with session.post(
                        self.api_base,
                        headers=self.analysis_headers,
                        json=insight_payload,
                        timeout=30
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    insights = result['choices'][0]['message']['content']

                # 创建新的记忆对象
                reflection_memory = await self._create_memory(
                    content=f"[反思]\n问题：\n{questions}\n\n洞察：\n{insights}",
                    memory_type=MemoryType.REFLECTION
                )
                logger.info(f"创建反思记忆:\n{reflection_memory.content}")
                # 添加到记忆流
                self.memory_stream.add_memory(reflection_memory)

        except Exception as e:
            print(f"生成反思时发生错误: {str(e)}")

    def clear_history(self):
        """清空对话历史和记忆"""
        self.dialogue_window = DialogueWindow(self.dialogue_window.max_size)
        self.memory_stream = MemoryStream()
        self._unprocessed_messages_count = 0  # 重置未处理消息计数


async def main():
    """主函数：演示如何使用EnhancedChat"""
    # 配置信息
    API_KEY = "sk-8bc9b3c811104f9480d5e054601b9c8e"
    ANALYSIS_API_KEY = "sk-0fa801059aab4aefbd262b8cbccaa159"
    EMBEDDING_API_KEY = "9a9c269a4914924d102c116e2e5e1977.aTo5260Pgma7epzh"

    # 初始化服务
    embedding_service = EmbeddingService(EMBEDDING_API_KEY)
    importance_analyzer = ImportanceAnalyzer(ANALYSIS_API_KEY)

    # 创建聊天实例
    chat = EnhancedChat(
        api_key=API_KEY,
        analysis_api_key=ANALYSIS_API_KEY,
        # initial_system_message=INITIAL_SYSTEM_MSG,
        embedding_service=embedding_service,
        importance_analyzer=importance_analyzer
    )

    print("欢迎使用增强版AI助手！(输入 'quit' 退出，'clear' 清空历史)")

    # 选择初始话题并开始对话
    initial_question = await chat.select_initial_topic()
    print(f"\n=== 开始采访 ===")
    print(f"\n助手: {initial_question}")

    while True:
        user_input = input("\n用户: ").strip()

        if user_input.lower() == 'quit':
            break
        elif user_input.lower() == 'clear':
            chat.clear_history()
            print("历史已清空！")
            continue
        elif not user_input:
            continue

        response = await chat.chat(user_input)
        print(f"\n助手: {response}")


if __name__ == "__main__":
    asyncio.run(main())
