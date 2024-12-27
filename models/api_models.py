from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class ChatRequest(BaseModel):
    """聊天请求模型"""
    user_input: str


class ChatResponse(BaseModel):
    """聊天响应模型"""
    response: str
    unit_id: Optional[str] = None


class DialogueEntry(BaseModel):
    """对话条目模型"""
    role: str
    content: str
    timestamp: str = None

    def __init__(self, **data):
        if "timestamp" not in data:
            data["timestamp"] = datetime.now().isoformat()
        super().__init__(**data)


class ImportDialogueRequest(BaseModel):
    """导入对话请求模型"""
    dialogue_history: List[DialogueEntry]


class ImportDialogueResponse(BaseModel):
    """导入对话响应模型"""
    unit_id: str


class WorkflowStatus(BaseModel):
    """工作流状态模型"""
    id: str
    type: str
    status: str
    create_time: str
    node_states: dict
    error: Optional[str] = None
    svg_ready: bool


class SVGResult(BaseModel):
    """SVG结果模型"""
    content: str  # SVG内容字符串
    type: str  # 结果类型
    metadata: dict  # 元数据
