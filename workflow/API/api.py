from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from workflow.core.workflow_manager import WorkflowManager
from workflow.core.node_types import (ConversationNode, NarrativeNode, 
                                    AnalysisNode, SVGNode)
import asyncio
import subprocess
import sys
import logging
import os
import time

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
        import os

        # 确保临时文件目录存在
        temp_dir = os.path.join(os.getcwd(), 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        # 创建临时文件
        temp_file = os.path.join(temp_dir, f'workflow_input_{os.getpid()}.json')
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(initial_input, f, ensure_ascii=False, indent=2)
        logger.info(f"创建临时文件: {temp_file}")

        # 获取run_monitor.py的完整路径
        monitor_script = os.path.abspath("run_monitor.py")
        if not os.path.exists(monitor_script):
            raise FileNotFoundError(f"找不到监控程序脚本: {monitor_script}")

        # 启动监控程序
        cmd = [sys.executable, monitor_script, "--input", temp_file]
        logger.info(f"执行命令: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd,
            # 不捕获输出，让它显示在控制台
            stdout=None,
            stderr=None,
            shell=False,
            env=os.environ.copy()
        )
        logger.info("已启动监控程序")

        # 等待一小段时间检查进程状态
        time.sleep(2)
        
        if process.poll() is not None:
            # 如果进程已退出，获取错误信息
            error_msg = "监控程序意外退出"
            raise RuntimeError(f"监控程序启动失败: {error_msg}")

        return process

    except Exception as e:
        logger.error(f"无法打开监控界面: {str(e)}")
        # 清理临时文件
        try:
            if 'temp_file' in locals():
                os.remove(temp_file)
        except:
            pass
        raise

@app.post("/start_workflow")
async def start_workflow(request: WorkflowRequest):
    try:
        logger.info("收到工作流请求")
        logger.info(f"对话历史: {request.conversation_history}")
        logger.info(f"是否可视化: {request.visualize}")

        # 准备初始输入数据
        initial_input = {
            "conversation_history": request.conversation_history
        }

        # 如果需要可视化，打开监控界面
        if request.visualize:
            logger.info("正在启动可视化界面")
            try:
                open_monitor(initial_input)
                # 返回成功响应
                return {"status": "success", "message": "监控界面已启动"}
            except Exception as e:
                logger.error(f"启动监控界面失败: {str(e)}")
                raise HTTPException(status_code=500, detail=f"启动监控界面失败: {str(e)}")

        # 否则直接执行工作流
        logger.info("开始执行工作流")
        try:
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
            logger.error(f"工作流执行失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"工作流执行失败: {str(e)}")

    except Exception as e:
        logger.error(f"执行过程发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 