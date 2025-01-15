from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import math
import aiohttp
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from zhipuai import ZhipuAI
import logging
import random
from functools import lru_cache, wraps
import hashlib
import hnswlib
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
import pickle
import os
import time

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


# timer_decorator: 性能监控装饰器
# 作用：监控异步和同步函数的执行时间
# 参数：
#   - func: 被装饰的函数
# 返回：包装后的函数，会记录执行时间
def timer_decorator(func):
    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time
            logger.info(f"函数 {func.__name__} 执行时间: {execution_time:.4f} 秒")
            return result

        return async_wrapper
    else:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time
            logger.info(f"函数 {func.__name__} 执行时间: {execution_time:.4f} 秒")
            return result

        return sync_wrapper


# 1. 首先定义基础的数据结构

class MemoryType(Enum):
    """记忆类型枚举
    DIALOGUE: 对话内容的记忆
    REFLECTION: AI系统生成的反思和洞察
    """
    DIALOGUE = "dialogue"
    REFLECTION = "reflection"


@dataclass
class Memory:
    """记忆对象，存储单条记忆的数据结构
    
    属性:
        content (str): 记忆的具体内容
        timestamp (datetime): 记忆创建时间
        last_access (datetime): 最后一次访问时间，用于计算时间衰减
        importance (float): 重要性评分(1-10)，由ImportanceAnalyzer评估
        embedding (List[float]): 内容的向量表示，用于相似度检索
        memory_type (MemoryType): 记忆类型(对话/反思)
    """
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
    """记忆流管理器：管理、存储和检索记忆
    
    主要功能：
    1. 使用HNSW索引进行高效的向量相似度检索
    2. 实现基于时间衰减的记忆检索
    3. 结合重要性、相关性和时间衰减进行综合排序
    
    关键参数：
        decay_factor (float): 时间衰减因子，控制记忆随时间衰减的速度
        score_threshold (float): 记忆检索的分数阈值
    """

    def __init__(self, decay_factor: float = 0.995, score_threshold: float = 0.6):
        """
       初始化记忆流管理器
       decay_factor: 时间衰减因子
       score_threshold: 记忆分数阈值
       """
        self.memories: List[Memory] = []
        self.decay_factor = decay_factor
        self.score_threshold = score_threshold  # 添加分数阈值

        # 初始化HNSW索引
        self.dim = 2048  # embedding维度
        self.index = hnswlib.Index(space='cosine', dim=self.dim)
        # ef_construction 影响索引构建质量，M影响索引大小和搜索速度
        self.index.init_index(max_elements=100000, ef_construction=200, M=16)
        self.index.set_ef(50)  # ef影响搜索精度和速度

        # 用于将memory id映射到实际memory对象
        self.id_to_memory = {}
        self.current_id = 0

    def add_memory(self, memory: Memory):
        """添加新的记忆并更新索引"""
        if memory.embedding is None:
            logger.warning("Memory没有embedding，跳过索引更新")
            return

        # 添加维度检查
        if len(memory.embedding) != self.dim:
            logger.error(f"Embedding维度不匹配: 期望{self.dim}, 实际{len(memory.embedding)}")
            return

        try:
            # 确保输入格式正确
            embedding_array = np.array([memory.embedding], dtype=np.float32)
            id_array = np.array([self.current_id])

            self.index.add_items(embedding_array, id_array)
            self.memories.append(memory)
            self.id_to_memory[self.current_id] = memory
            self.current_id += 1

        except Exception as e:
            logger.error(f"添加向量到索引时发生错误: {str(e)}")
            raise

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

    @timer_decorator
    def retrieve_memories(self,
                          query_embedding: List[float],
                          top_k: int = 3,
                          recency_weight: float = 1.0,
                          importance_weight: float = 1.0,
                          relevance_weight: float = 1.0) -> List[Memory]:
        """检索相关记忆
        
        参数:
            query_embedding (List[float]): 查询内容的向量表示
            top_k (int): 返回的记忆数量
            recency_weight (float): 时间衰减权重
            importance_weight (float): 重要性权重
            relevance_weight (float): 相关性权重
        
        返回:
            List[Memory]: 按综合得分排序的记忆列表
        """
        if not self.memories:
            return []

        # 检查查询向量维度
        if len(query_embedding) != self.dim:
            logger.error(f"查询向量维度不匹配: 期望{self.dim}, 实际{len(query_embedding)}")
            return []

        # 使用HNSW进行快速近邻搜索
        query_vector = np.array([query_embedding])
        labels, distances = self.index.knn_query(query_vector, k=min(top_k * 2, len(self.memories)))

        # 计算综合分数并排序
        scores = []
        for idx, distance in zip(labels[0], distances[0]):
            memory = self.id_to_memory[idx]

            # 计算各个维度的分数
            recency_score = self._calculate_recency(memory)
            relevance_score = 1 - distance  # 将距离转换为相似度
            importance_score = memory.importance / 10.0

            # 计算加权总分
            final_score = (recency_weight * recency_score +
                           importance_weight * importance_score +
                           relevance_weight * relevance_score) / (
                                  recency_weight + importance_weight + relevance_weight)

            logger.info(f"""
            记忆评分详情:
            - 内容: {memory.content[:50]}...
            - Recency: {recency_score:.4f}
            - Importance: {importance_score:.4f}
            - Relevance: {relevance_score:.4f}
            - Final Score: {final_score:.4f}
            """)

            if final_score >= self.score_threshold:
                scores.append((final_score, memory))

        # 排序并返回top_k个记忆
        scores.sort(key=lambda x: x[0], reverse=True)
        retrieved_memories = [memory for _, memory in scores[:top_k]]

        logger.info(f"""
        检索结果统计(Top {top_k}):
        - 总记忆数: {len(self.memories)}
        - 通过阈值数: {len(scores)}
        - 最终返回数: {len(retrieved_memories)}
        {'=' * 50}""")

        return retrieved_memories

    def save_index(self, path: str):
        """保存索引到文件"""
        self.index.save_index(path)

    def load_index(self, path: str):
        """从文件加载索引"""
        self.index.load_index(path)


class EmbeddingCache:
    def __init__(self, capacity=1000):
        self.cache = {}
        self.capacity = capacity

    def _get_hash(self, text: str) -> str:
        """生成文本的哈希值作为缓存键"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def get(self, text: str) -> Optional[List[float]]:
        """获取缓存的embedding"""
        return self.cache.get(self._get_hash(text))

    def set(self, text: str, embedding: List[float]):
        """设置embedding缓存"""
        if len(self.cache) >= self.capacity:
            # 简单的LRU策略：删除第一个元素
            self.cache.pop(next(iter(self.cache)))
        self.cache[self._get_hash(text)] = embedding


class EmbeddingService:
    """文本向量化服务
    
    功能：
    1. 调用智谱AI的embedding接口获取文本向量表示
    2. 实现向量缓存以提高性能
    3. 支持批量处理
    
    关键属性：
        model (str): 使用的embedding模型
        cache (EmbeddingCache): 向量缓存器
        expected_dim (int): 向量维度(2048)
    """

    def __init__(self, api_key: str):
        self.client = ZhipuAI(api_key=api_key)
        self.model = "embedding-3"
        self.cache = EmbeddingCache()
        self.expected_dim = 2048  # 添加预期维度

    @timer_decorator
    async def get_embedding(self, text: Union[str, List[str]]) -> List[float]:
        """获取文本的向量嵌入"""

        # 确保输入是字符串
        if isinstance(text, list):
            text = text[0]

        # 检查缓存
        cached_embedding = self.cache.get(text)
        if cached_embedding is not None:
            if len(cached_embedding) == self.expected_dim:
                logger.info("使用缓存的embedding")
                return cached_embedding

        try:
            # 调用智谱AI的embedding接口
            response = self.client.embeddings.create(
                input=text,
                model=self.model
            )
            embedding = response.data[0].embedding

            # 验证维度
            if len(embedding) != self.expected_dim:
                logger.error(f"API返回的embedding维度不正确: {len(embedding)}")
                return [0.0] * self.expected_dim

            # 存入缓存
            self.cache.set(text, embedding)

            # 返回embedding向量
            return embedding

        except Exception as e:
            print(f"获取embedding时发生错误: {str(e)}")
            # 返回一个空向量作为fallback
            return [0.0] * 2048  # 根据模型维度调整

    @timer_decorator
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
            return [[0.0] * 2048 for _ in texts]  # 根据模型维度调整


class ImportanceAnalyzer:
    """内容重要性分析服务
    
    功能：
    1. 分析文本内容的重要性
    2. 返回1-10的重要性评分
    
    评估标准：
    - 情感强度
    - 信息密度
    - 事件重要性
    - 关系影响
    """

    def __init__(self, api_key: str, api_base: str = "https://api.deepseek.com/v1/chat/completions"):
        self.api_key = api_key
        self.api_base = api_base
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    @timer_decorator
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
                    json=payload,
                    ssl=False  # 尝试禁用SSL验证
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
    """增强型对话系统
    
    核心功能：
    1. 基于记忆的上下文感知对话
    2. 自动生成对话反思和洞察
    3. 记忆的存储与检索
    4. 性能监控
    
    关键组件：
        memory_stream (MemoryStream): 记忆管理器
        dialogue_window (DialogueWindow): 对话历史管理
        embedding_service (EmbeddingService): 向量化服务
        importance_analyzer (ImportanceAnalyzer): 重要性分析器
    """

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

    @timer_decorator
    async def chat(self, user_input: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """处理用户输入并生成回复
        
        处理流程：
        1. 获取用户输入的向量表示
        2. 检索相关记忆
        3. 构建包含记忆的prompt
        4. 调用LLM生成回复
        5. 更新记忆和对话历史
        6. 触发异步反思（如果需要）
        
        性能监控：
        - Embedding API调用时间
        - 记忆检索时间
        - Prompt构建时间
        - LLM API调用时间
        - 记忆更新时间
        - 总体执行时间
        """
        try:
            total_start = time.time()
            logger.info(f"收到用户输入: {user_input}")

            # 更新对话窗口
            self.dialogue_window.add_message("user", user_input)
            self._unprocessed_messages_count += 1  # 增加未处理消息计数

            embedding_start = time.time()
            query_embedding = await self.embedding_service.get_embedding(user_input)
            logger.info(f"[性能] Embedding API调用耗时: {time.time() - embedding_start:.2f}秒")

            # 使用获取到的embedding检索相关记忆
            retrieval_start = time.time()
            relevant_memories = self.memory_stream.retrieve_memories(
                query_embedding=query_embedding,
                top_k=3,
                recency_weight=0.6,
                importance_weight=0.8,
                relevance_weight=1.0
            )
            logger.info(f"[性能] 记忆检索耗时: {time.time() - retrieval_start:.2f}秒")
            prompt_start = time.time()
            memory_prompt = self._format_memories_for_prompt(relevant_memories)
            logger.info(f"检索到{len(relevant_memories)}条相关记忆")
            # 记录检索到的记忆详情
            logger.info("\n=== 检索到的相关记忆 ===")
            for i, memory in enumerate(relevant_memories, 1):
                logger.info(f"""
                       记忆 {i}:
                       - 内容: {memory.content[:100]}...
                       - 时间: {memory.timestamp}
                       - 重要性: {memory.importance}
                       - 最后访问: {memory.last_access}
                       """)

            # 构建完整的prompt
            messages = [
                self.system_message,
                {"role": "system", "content": memory_prompt},
                *self.dialogue_window.get_messages()
            ]
            logger.info(f"[性能] Prompt构建耗时: {time.time() - prompt_start:.2f}秒")
            logger.info(f"构建的prompt包含{len(messages)}条消息")

            async def get_assistant_response():
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
                            json=payload,
                            ssl=False  # 尝试禁用SSL验证
                    ) as response:
                        response.raise_for_status()
                        result = await response.json()
                        return result['choices'][0]['message']['content']

            # 获取助手响应
            api_start = time.time()
            assistant_response = await get_assistant_response()
            logger.info(f"[性能] LLM API调用耗时: {time.time() - api_start:.2f}秒")

            # 创建临时记忆对象（使用默认重要性）
            memory_start = time.time()
            temp_memory = Memory(
                content=user_input,
                timestamp=datetime.now(),
                last_access=datetime.now(),
                importance=5.0,  # 默认中等重要性
                embedding=query_embedding,
                memory_type=MemoryType.DIALOGUE
            )
            logger.info(f"[性能] 记忆创建和存储耗时: {time.time() - memory_start:.2f}秒")

            # 添加到记忆流
            self.memory_stream.add_memory(temp_memory)

            # 在后台启动重要性分析任务
            asyncio.create_task(self._update_memory_importance(user_input, temp_memory))

            # 更新对话窗口
            self.dialogue_window.add_message("assistant", assistant_response)

            # 触发异步思考
            if self._unprocessed_messages_count >= self.REFLECTION_THRESHOLD:
                asyncio.create_task(self._generate_reflection())
                self._unprocessed_messages_count = 0

            logger.info(f"[性能] 总耗时: {time.time() - total_start:.2f}秒")
            return assistant_response

        except Exception as e:
            return f"发生错误: {str(e)}"

    async def _update_memory_importance(self, content: str, memory: Memory):
        """后台更新记忆的重要性分数"""
        try:
            # 获取重要性分数
            importance = await self.importance_analyzer.analyze_importance(content)

            # 更新记忆对象的重要性分数
            memory.importance = importance
            logger.info(f"已更新记忆重要性分数: {importance}")

        except Exception as e:
            logger.error(f"更新记忆重要性时发生错误: {str(e)}")

    @timer_decorator
    async def _generate_reflection(self):
        """生成对话反思和洞察
        
        处理流程：
        1. 收集最近的用户消息
        2. 生成高级分析问题
        3. 基于问题生成洞察
        4. 将洞察存储为反思类型的记忆
        
        触发条件：
        - 累积一定数量的新消息(REFLECTION_THRESHOLD)
        """
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
                        ssl=False,  # 尝试禁用SSL验证
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
                        timeout=30,
                        ssl=False  # 尝试禁用SSL验证
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
    API_KEY = "sk-5517c184b951429abc32db010baeba0d"
    ANALYSIS_API_KEY = "sk-dbc014c9dbad4e7fbc7ca68211af0d38"
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
