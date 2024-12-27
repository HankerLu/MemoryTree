import asyncio
import json
from datetime import datetime
import logging
import pytest

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from workflow.service import WorkflowService
from services.chat_service import ChatService

@pytest.mark.asyncio
async def test_chat_simulation():
    """模拟真实对话场景"""
    # 初始化服务
    workflow_service = WorkflowService()
    chat_service = ChatService(workflow_service.workflow_manager)
    
    # 记录工作流ID
    workflow_ids = []
    
    # 1. 模拟快速对话
    conversations = [
        "你好，我想聊聊我的经历",
        "我最近在学习编程",
        "Python很有趣",
        "我已经学会了基础语法",
        "现在正在学习异步编程",  # 第5轮，应该触发工作流
        "这些知识很实用",
        "我打算继续深入学习"     # 新的对话开始累积
    ]
    
    try:
        # 2. 执行对话
        for message in conversations:
            result = await chat_service.chat(message)
            logging.info(f"用户: {message}")
            logging.info(f"AI: {result['response']}")
            
            # 如果触发了工作流，记录ID
            if "unit_id" in result:
                workflow_ids.append(result["unit_id"])
                logging.info(f"触发工作流: {result['unit_id']}")
        
        # 3. 检查工作流状态
        for unit_id in workflow_ids:
            max_retries = 10
            retry_count = 0
            
            while retry_count < max_retries:
                status = await workflow_service.get_workflow_status(unit_id)
                logging.info(f"工作流 {unit_id} 状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
                
                if status["status"] == "completed":
                    # 获取SVG结果
                    svg_result = await workflow_service.get_svg_result(unit_id)
                    logging.info(f"工作流 {unit_id} SVG生成完成")
                    assert svg_result is not None
                    break
                    
                elif status["status"] == "failed":
                    logging.error(f"工作流 {unit_id} 执行失败: {status.get('error')}")
                    break
                    
                retry_count += 1
                await asyncio.sleep(1)
                
            assert retry_count < max_retries, f"工作流 {unit_id} 执行超时"
        
        # 4. 验证触发机制
        assert len(workflow_ids) > 0, "没有工作流被触发"
        logging.info(f"总共触发了 {len(workflow_ids)} 个工作流")
        
    except Exception as e:
        logging.error(f"测试过程出错: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_import_simulation():
    """模拟导入历史对话场景"""
    workflow_service = WorkflowService()
    chat_service = ChatService(workflow_service.workflow_manager)
    
    # 准备历史对话数据
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
        # 导入对话并触发工作流
        unit_id = await chat_service.import_dialogue(dialogue_history)
        logging.info(f"导入对话触发工作流: {unit_id}")
        
        # 等待工作流完成
        max_retries = 10
        retry_count = 0
        
        while retry_count < max_retries:
            status = await workflow_service.get_workflow_status(unit_id)
            logging.info(f"导入工作流状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
            
            if status["status"] == "completed":
                svg_result = await workflow_service.get_svg_result(unit_id)
                logging.info("导入工作流SVG生成完成")
                assert svg_result is not None
                break
                
            elif status["status"] == "failed":
                logging.error(f"导入工作流执行失败: {status.get('error')}")
                break
                
            retry_count += 1
            await asyncio.sleep(1)
            
        assert retry_count < max_retries, "导入工作流执行超时"
        
    except Exception as e:
        logging.error(f"导入测试过程出错: {str(e)}")
        raise 