from typing import Dict, Any, Optional, List
from datetime import datetime

from app import logger
from workflow.core.workflow_manager import WorkflowManager
from agents.conversation_agent import ConversationAgent


class ChatService:
    """
    聊天服务：处理用户对话并管理工作流触发
    - 处理用户实时对话
    - 维护对话历史
    - 检查触发条件
    - 触发工作流处理
    """

    def __init__(self, workflow_manager):
        self.workflow_manager = workflow_manager
        self.conversation_agent = ConversationAgent()  # 初始化对话代理
        self.chat_history = self.conversation_agent.get_conversation_history()
        self.message_count = 1
        self.trigger_threshold = 5  # 每5条消息触发一次工作流

    async def chat(self, user_input: str) -> Dict[str, Any]:
        """处理用户输入，返回AI响应"""
        try:
            # 添加用户消息
            self.chat_history.append({
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now().isoformat()
            })
            self.message_count += 1

            # 生成AI响应
            response = self.conversation_agent.chat(user_input)
            self.chat_history.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().isoformat()
            })
            self.message_count += 1

            result = {"response": response}

            # 检查是否需要触发工作流
            if self.message_count >= self.trigger_threshold:
                unit_id = await self.workflow_manager.create_work_unit(
                    {"dialogue_history": self.chat_history},
                    "realtime"
                )
                result["unit_id"] = unit_id
                # 重置计数
                self.message_count = 0

            return result

        except Exception as e:
            logger.error(f"聊天处理失败: {str(e)}")
            raise

    def _check_trigger_condition(self) -> bool:
        """检查是否满足触发条件"""
        return self.dialogue_count >= self.trigger_threshold

    async def _trigger_workflow(self) -> str:
        """
        触发工作流处理
        Returns:
            工作单元ID
        """
        return await self.workflow_manager.create_work_unit(
            data={
                "dialogue_history": self.current_dialogue.copy(),
                "create_time": datetime.now()
            },
            unit_type="realtime"
        )

    async def import_dialogue(self, dialogue_history: List[Dict]) -> str:
        """
        导入历史对话并���发工作流
        Args:
            dialogue_history: 历史对话列表
        Returns:
            工作单元ID
        """
        return await self.workflow_manager.create_work_unit(
            data={
                "dialogue_history": dialogue_history,
                "create_time": datetime.now()
            },
            unit_type="import"
        )

    def get_dialogue_history(self) -> List[Dict]:
        """获取当前对话历史"""
        return self.current_dialogue.copy()

    def clear_history(self):
        """清空当前对话历史"""
        prompt_template = """你是一位专业的回忆录采访者。你的任务是通过对话的方式，引导用户回忆和分享他们人生中的重要经历、情感和故事。

        请遵循以下原则：
        1. 以温和友善的态度与用户交谈，营造轻松舒适的氛围
        2. 循序渐进地引导用户展开回忆，从简单的话题逐渐深入
        3. 针对用户提到的关键事件、人物或情感进行追问，获取更丰富的细节
        4. 适时给予共情回应，鼓励用户表达真实的想法和感受
        5. 注意保护用户隐私，对敏感话题保持谨慎

        你的目标是帮助用户梳理生命历程中的重要片段，收集有价值的回忆素材，为创作一部完整的回忆录做准备。"""
        messages = [
            {"role": "system", "content": prompt_template}
        ]
        self.current_dialogue = messages
        self.dialogue_count = 1
