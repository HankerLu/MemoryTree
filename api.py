from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from workflow.core.workflow_manager import WorkflowManager
from workflow.core.node_types import (ConversationNode, NarrativeNode, 
                                    AnalysisNode, SVGNode)
import asyncio
import subprocess
import sys
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class WorkflowRequest(BaseModel):
    conversation_history: list
    visualize: bool = False  # 是否打开可视化界面

def open_monitor(initial_input: dict):
    """打开监控界面"""
    try:
        # 将初始输入保存到临时文件
        import json
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(initial_input, f)
            temp_file = f.name
        logger.info(f"创建临时文件: {temp_file}")

        # 传递临时文件路径给监控程序
        subprocess.Popen([sys.executable, "run_monitor.py", "--input", temp_file])
        logger.info("已启动监控程序")
    except Exception as e:
        logger.error(f"无法打开监控界面: {str(e)}")
        raise

@app.post("/start_workflow")
async def start_workflow(request: WorkflowRequest):
    try:
        logger.info("收到工作流请求")
        logger.info(f"对话历史: {request.conversation_history}")
        logger.info(f"是否可视化: {request.visualize}")

        # 准备初始输入数据
        initial_input = {
            "user_input": request.conversation_history[-1] if request.conversation_history else "",
            "conversation_history": request.conversation_history
        }

        # 如果需要可视化，打开监控界面
        if request.visualize:
            logger.info("正在启动可视化界面")
            open_monitor(initial_input)
            return {"status": "success", "message": "监控界面已启动"}

        # 否则直接执行工作流
        logger.info("开始执行工作流")
        manager = WorkflowManager()
        # 使用实际的节点而不是mock
        manager.add_node("conversation", "对话节点", ConversationNode()._process)
        manager.add_node("narrative", "叙事体生成", NarrativeNode()._process)
        manager.add_node("analysis", "综合分析", AnalysisNode()._process)
        manager.add_node("svg", "SVG卡片生成", SVGNode()._process)

        # 执行工作流
        result = await manager.execute_workflow(initial_input)
        logger.info("工作流执行完成")
        return {
            "status": "success", 
            "result": result,
            "svg_content": result.get("svg_content", "")
        }

    except Exception as e:
        logger.error(f"执行过程中发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 