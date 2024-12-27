import pytest
from fastapi.testclient import TestClient
import json
from datetime import datetime
import logging
import asyncio

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from app import app

# 创建测试客户端
client = TestClient(app)

@pytest.mark.asyncio
async def test_chat_workflow(client):
    """测试聊天API和工作流程"""
    # 1. 发送聊天请求
    chat_response = client.post(
        "/chat",
        json={"user_input": "你好，我想聊聊我的经历"}
    )
    assert chat_response.status_code == 200
    chat_data = chat_response.json()
    assert "response" in chat_data
    logging.info(f"聊天响应: {chat_data}")
    
    # 如果触发了工作流，测试工作流状态
    if "unit_id" in chat_data:
        unit_id = chat_data["unit_id"]
        logging.info(f"工作流ID: {unit_id}")
        
        # 2. 查询工作流状态
        max_retries = 10
        for i in range(max_retries):
            status_response = client.get(f"/workflow/{unit_id}/status")
            assert status_response.status_code == 200
            status_data = status_response.json()
            logging.info(f"工作流状态: {json.dumps(status_data, indent=2)}")
            
            if status_data["status"] == "completed":
                # 3. 获取SVG结果
                svg_response = client.get(f"/workflow/{unit_id}/svg")
                assert svg_response.status_code == 200
                svg_data = svg_response.json()
                logging.info("SVG生成成功")
                assert "content" in svg_data
                break
                
            elif status_data["status"] == "failed":
                pytest.fail(f"工作流执行失败: {status_data.get('error')}")
                
            await asyncio.sleep(1)
        else:
            pytest.fail("工作流执行超时")

@pytest.mark.asyncio
async def test_import_dialogue():
    """测试导入对话API"""
    # 1. 准备导入数据
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
    
    # 2. 发送导入请求
    import_response = client.post(
        "/import-dialogue",
        json={"dialogue_history": dialogue_history}
    )
    assert import_response.status_code == 200
    import_data = import_response.json()
    assert "unit_id" in import_data
    unit_id = import_data["unit_id"]
    logging.info(f"导入工作流ID: {unit_id}")
    
    # 3. 查询工作流状态
    max_retries = 10
    for i in range(max_retries):
        status_response = client.get(f"/workflow/{unit_id}/status")
        assert status_response.status_code == 200
        status_data = status_response.json()
        logging.info(f"导入工作流状态: {json.dumps(status_data, indent=2)}")
        
        if status_data["status"] == "completed":
            # 4. 获取SVG结果
            svg_response = client.get(f"/workflow/{unit_id}/svg")
            assert svg_response.status_code == 200
            svg_data = svg_response.json()
            logging.info("导入SVG生成成功")
            assert "content" in svg_data
            break
            
        elif status_data["status"] == "failed":
            pytest.fail(f"导入工作流执行失败: {status_data.get('error')}")
            
        await asyncio.sleep(1)
    else:
        pytest.fail("导入工作流执行超时")

@pytest.mark.asyncio
async def test_error_handling():
    """测试错误处理"""
    # 1. 测试无效的聊天请求
    response = client.post(
        "/chat",
        json={}  # 缺少必要字段
    )
    assert response.status_code == 422  # FastAPI的验证错误
    
    # 2. 测试无效的工作流ID
    response = client.get("/workflow/invalid-id/status")
    assert response.status_code == 404
    
    # 3. 测试无效的导入数据
    response = client.post(
        "/import-dialogue",
        json={"dialogue_history": []}  # 空对话历史
    )
    assert response.status_code == 500  # 服务器内部错误
    error_data = response.json()
    assert "detail" in error_data 