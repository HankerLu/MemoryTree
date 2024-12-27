from typing import Dict, Any, List
from datetime import datetime
from .node import BaseNode
from agents.conversation_agent import ConversationAgent
from agents.narrative_agent import NarrativeAgent
from agents.sentence_analyzer_agent import SentenceAnalyzerAgent
from agents.tag_analyzer_agent import TagAnalyzerAgent
from services.book_svg_service import BookSVGService
import logging
import json

from database.base import get_db
from services.conversation_service import ConversationService
from services.narrative_service import NarrativeService
from services.paragraph_service import ParagraphService
from services.tag_service import TagService
from entities.narrative import Narrative
from entities.paragraph import Paragraph
from entities.tag import Tag

logger = logging.getLogger(__name__)


class ConversationNode(BaseNode):
    """对话处理节点：处理对话历史，准备生成叙事体的数据"""

    def __init__(self):
        super().__init__("conversation")
        self.agent = ConversationAgent()

    async def _process(self, work_unit: Dict[str, Any]) -> Dict[str, Any]:
        """处理对话历史"""
        logger.info(f"ConversationNode 接收到输入: {work_unit}")

        dialogue_history = work_unit["data"].get("dialogue_history", [])
        if isinstance(dialogue_history, str):
            dialogue_history = json.loads(dialogue_history)

        # 处理对话历史，生成结构化数据
        structured_dialogue = []
        for entry in dialogue_history:
            structured_dialogue.append({
                "role": entry["role"],
                "content": entry["content"],
                "timestamp": entry.get("timestamp", datetime.now().isoformat())
            })

        return {
            "dialogue": structured_dialogue,
            "metadata": {
                "dialogue_count": len(structured_dialogue),
                "process_time": datetime.now().isoformat()
            }
        }


class NarrativeNode(BaseNode):
    """叙事生成节点：根据处理后的对话生成叙事文本"""

    def __init__(self):
        super().__init__("narrative")
        self.agent = NarrativeAgent()

    async def process(self, work_unit: Dict[str, Any]) -> Dict[str, Any]:
        """叙事生成节点"""
        try:
            # 验证工作单元
            if not work_unit or "id" not in work_unit:
                raise ValueError("无效的工作单元：缺少ID")

            # 获取对话历史
            dialogue = work_unit["data"].get("dialogue_history", [])

            # 生成叙事文本
            narrative_text = self.agent.generate_narrative(dialogue)

            # 确保结果字典存在
            if "results" not in work_unit:
                work_unit["results"] = {}

            # 更新工作单元结果
            work_unit["results"]["narrative"] = {
                "content": narrative_text,
                "type": "chapter",
                "metadata": {
                    "source_dialogue_count": len(dialogue),
                    "generate_time": datetime.now().isoformat()
                }
            }

            return work_unit

        except Exception as e:
            logger.error(f"叙事生成失败: {str(e)}")
            raise


class SVGNode(BaseNode):
    """SVG生成节点：根据叙事文本生成可视化卡片"""

    def __init__(self):
        super().__init__("svg")
        self.svg_service = BookSVGService()

    async def process(self, work_unit: Dict[str, Any]) -> Dict[str, Any]:
        """SVG生成节点"""
        try:
            # 获取叙事内容
            narrative = work_unit.get("results", {}).get("narrative", {})
            if not narrative or "content" not in narrative:
                raise ValueError("缺少叙事内容")

            narrative_content = narrative.get("content")
            if not isinstance(narrative_content, str):
                raise ValueError(f"无效的叙事内容类型: {type(narrative_content)}")

            if not narrative_content.strip():
                raise ValueError("叙事内容为空")

            logger.info(f"准备生成SVG，内容长度: {len(narrative_content)}")

            # 生成SVG
            svg_content = self.svg_service.generate_svg(
                number="Chapter 1",  # 可以根据实际需求设置
                title="回忆录",  # 可以从narrative中提取
                content=narrative["content"],
                is_chapter=False
            )

            # 更新工作单元结果
            work_unit["results"]["svg"] = {
                "content": svg_content,  # BookSVGService返回的是列表，取第一个
                "type": "memory_tree",
                "metadata": {
                    "generate_time": datetime.now().isoformat(),
                    "source_narrative": len(narrative["content"])
                }
            }

            return work_unit

        except Exception as e:
            logger.error(f"SVG生成失败: {str(e)}")
            raise


class AnalysisNode(BaseNode):
    """分析节点：分析叙事文本并进行持久化"""

    def __init__(self):
        super().__init__("analysis")
        self.sentence_agent = SentenceAnalyzerAgent()
        self.tag_agent = TagAnalyzerAgent()
        # 初始化服务
        self.conversation_service = ConversationService()
        self.narrative_service = NarrativeService()
        self.paragraph_service = ParagraphService()
        self.tag_service = TagService()

    async def process(self, work_unit: Dict[str, Any]) -> Dict[str, Any]:
        """分析节点"""
        try:
            # 从上游节点获取处理结果
            narrative_content = work_unit["results"]["narrative"]["content"]
            dialogue_history = work_unit["data"]["dialogue_history"]
            session_id = work_unit["id"]  # 使用工作单元ID作为会话ID

            # 分析处理
            sentence_result = self.sentence_agent.analyze_narrative(narrative_content)
            paragraphs = self.sentence_agent.get_paragraphs(sentence_result)

            tag_result = self.tag_agent.analyze_tags(narrative_content)
            tags = self.tag_agent.parse_tags(tag_result)

            # 直接使用已有的分析结果
            merged_results = []
            for p, t in zip(paragraphs, tags):
                merged_results.append({
                    'content': p['text'],
                    'type': p['type'],
                    'tags': t.get('tags', {})
                })

            if not merged_results:
                raise Exception("合并失败")

            # 在事务中执行所有持久化操作
            with get_db() as db:
                try:
                    # 设置所有服务使用同一个会话
                    self.conversation_service._session = db
                    self.narrative_service._session = db
                    self.paragraph_service._session = db
                    self.tag_service._session = db

                    # 3.1 保存对话历史
                    if not self.conversation_service.save_history(session_id, dialogue_history):
                        raise Exception("保存对话历史失败")

                    # 3.2 保存叙事体
                    narrative = Narrative(
                        session_id=session_id,
                        content=narrative_content
                    )
                    narrative = self.narrative_service.create(narrative)

                    # 3.3 保存段落和标签
                    for idx, result in enumerate(merged_results, 1):
                        # 创建段落
                        paragraph = Paragraph(
                            narrative_id=narrative.id,
                            content=result['content'],
                            sequence_number=idx,
                            paragraph_type=result['type']
                        )
                        paragraph = self.paragraph_service.create(paragraph)

                        # 处理标签
                        for dimension, tags in result['tags'].items():
                            for tag_value in tags:
                                # 查找或创建标签
                                existing_tag = self.tag_service.find_by_dimension_and_value(
                                    dimension, tag_value
                                )
                                if existing_tag:
                                    tag = existing_tag
                                else:
                                    tag = Tag(dimension=dimension, tag_value=tag_value)
                                    tag = self.tag_service.create(tag)

                                # 关联标签
                                paragraph.tags.append(tag)

                        # 更新段落
                        self.paragraph_service.update(paragraph)

                    # 提交事务
                    db.commit()

                except Exception as e:
                    db.rollback()  # 回滚事务
                    raise


        except Exception as e:
            logger.error(f"分析失败: {str(e)}")
            raise
