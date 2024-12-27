import asyncio
import json
from datetime import datetime
import logging
import pytest

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from workflow.service import WorkflowService
from services.chat_service import ChatService

@pytest.mark.asyncio
async def test_workflow():
    """测试工作流程"""
    # 1. 初始化服务
    workflow_service = WorkflowService()
    chat_service = ChatService(workflow_service.workflow_manager)
    
    # 2. 模拟对话数据
    dialogue_history = [
        {
            "role": "user",
            "content": "你好，我想聊聊我的经历",
            "timestamp": datetime.now().isoformat()
        },
        {
            "role": "assistant",
            "content": "好的，请告诉我你想分享什么",
            "timestamp": datetime.now().isoformat()
        },
        {
            "role": "user",
            "content": "我最近在学习编程",
            "timestamp": datetime.now().isoformat()
        }
    ]
    
    try:
        # 3. 导入对话并触发工作流
        unit_id = await chat_service.import_dialogue(dialogue_history)
        assert unit_id is not None, "工作单元创建失败"
        logging.info(f"创建工作单元: {unit_id}")
        
        # 4. 轮询检查状态
        max_retries = 10
        retry_count = 0
        
        while retry_count < max_retries:
            status = await workflow_service.get_workflow_status(unit_id)
            assert status is not None, "无法获取工作单元状态"
            logging.info(f"工作单元状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
            
            if status["status"] == "completed":
                # 5. 获取SVG结果
                svg_result = await workflow_service.get_svg_result(unit_id)
                assert svg_result is not None, "无法获取SVG结果"
                logging.info(f"SVG结果: {json.dumps(svg_result, indent=2, ensure_ascii=False)}")
                return
                
            elif status["status"] == "failed":
                raise AssertionError(f"工作流执行失败: {status.get('error', '未知错误')}")
                
            retry_count += 1
            await asyncio.sleep(1)
            
        raise AssertionError("工作流执行超时")
            
    except Exception as e:
        logging.error(f"测试过程出错: {str(e)}")
        raise 