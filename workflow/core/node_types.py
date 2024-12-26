from typing import Dict, Any
from .node import Node
from agents.conversation_agent import ConversationAgent
from agents.narrative_agent import NarrativeAgent
from agents.sentence_analyzer_agent import SentenceAnalyzerAgent
from agents.tag_analyzer_agent import TagAnalyzerAgent
from services.book_svg_service import BookSVGService
import logging

logger = logging.getLogger(__name__)

class ConversationNode(Node):
    """对话节点"""
    def __init__(self):
        super().__init__("conversation", "对话节点")
        self.agent = ConversationAgent()
        self.set_process_func(self._process)

    async def _process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理对话输入"""
        logger.info(f"ConversationNode 接收到输入: {input_data}")
        # 获取对话历史，确保是列表格式
        conversation_history = input_data.get("conversation_history", [])
        logger.info(f"ConversationNode 提取的对话历史: {conversation_history}")
        
        if isinstance(conversation_history, str):
            try:
                import json
                conversation_history = json.loads(conversation_history)
                logger.info("ConversationNode 解析字符串为JSON")
            except:
                logger.error("ConversationNode JSON解析失败")
                raise ValueError("对话历史必须是有效的JSON格式列表")

        self.agent.set_conversation_history(conversation_history)
        
        # 准备下一个节点需要的输入
        next_input = {
            "conversation": conversation_history
        }
        logger.info(f"ConversationNode 准备的下一个节点输入: {next_input}")

        result = {
            "raw_output": input_data.get("conversation_history", []),
            "processed_output": next_input.get("conversation", []),
            "conversation_history": conversation_history
        }
        logger.info(f"ConversationNode 返回结果: {result}")
        return result

class NarrativeNode(Node):
    """叙事体生成节点"""
    def __init__(self):
        super().__init__("narrative", "叙事体生成")
        self.agent = NarrativeAgent()
        self.set_process_func(self._process)

    async def _process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成叙事体"""
        logger.info(f"NarrativeNode 接收到输入: {input_data}")
        # 从上一个节点的processed_output中获取输入
        conversation = input_data.get("processed_output", {})
        logger.info(f"NarrativeNode 提取的对话数据: {conversation}")
        
        # 使用叙事代理处理
        logger.info(f"NarrativeNode 开始生成叙事体，输入类型: {type(conversation)}")
        raw_result = self.agent.generate_narrative(conversation)
        logger.info(f"NarrativeNode 生成的叙事体: {raw_result}")
        
        # 准备下一个节点需要的输入
        next_input = {
            "content": raw_result
        }
        logger.info(f"NarrativeNode 准备的下一个节点输入: {next_input}")

        result = {
            "raw_output": raw_result,
            "processed_output": next_input.get("content", ""),
            "narrative_metadata": raw_result
        }
        logger.info(f"NarrativeNode 返回结果: {result}")
        return result

class AnalysisNode(Node):
    """综合分析节点"""
    def __init__(self):
        super().__init__("analysis", "综合分析")
        self.sentence_agent = SentenceAnalyzerAgent()
        self.tag_agent = TagAnalyzerAgent()
        self.set_process_func(self._process)

    async def _process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析叙事体"""
        # 从上一个节点的processed_output中获取输入
        content = input_data.get("processed_output", {})
        
        # 1. 段落分析
        sentence_raw_result = self.sentence_agent.analyze_narrative(content)

        parse_sentence_raw_result = self.sentence_agent.get_paragraphs(sentence_raw_result)

        
        # 2. 标签分析
        tag_raw_result = self.tag_agent.analyze_tags(content)

        parse_tag_raw_result = self.tag_agent.parse_tags(tag_raw_result)

        try:
            merged_results = []
            for p, t in zip(parse_sentence_raw_result, parse_tag_raw_result):
                merged_results.append({
                    'content': p['text'],
                    'type': p['type'],
                    'tags': t.get('tags', {})
                })

            if not merged_results:
                return {}

            return {
                "raw_output": {
                    "sentence_analysis": sentence_raw_result,
                    "tag_analysis": tag_raw_result
                },
                "processed_output": merged_results

            }
        except Exception as e:
            raise ValueError(f"合并分析结果时发生错误：{str(e)}")
            return {}

class SVGNode(Node):
    """SVG卡片生成节点"""
    def __init__(self):
        super().__init__("svg", "SVG卡片生成")
        self.service = BookSVGService()
        self.set_process_func(self._process)

    async def _process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成SVG卡片"""
        # 从上一个节点的processed_output中获取输入
        # 这里需要改
        # content = input_data.get("processed_output", {}).get("content", "")
        # paragraphs = input_data.get("processed_output", {}).get("paragraphs", [])
        content = None
        
        # 生成SVG
        raw_result = self.service.generate_svg(
            number="Chapter 1",
            title="回忆录",
            content=content,
            is_chapter=True
        )
        
        return {
            "raw_output": raw_result,  # 原始SVG输出
            "processed_output": {
                "svg_content": raw_result
            }
        }