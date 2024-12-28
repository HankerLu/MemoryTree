from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from typing import Dict
from utils.logger import logger
from models.api_models import (
    ChatRequest,
    ChatResponse,
    ImportDialogueRequest,
    ImportDialogueResponse,
    WorkflowStatus,
    SVGResult
)
from workflow.service import WorkflowService
from services.chat_service import ChatService
from utils.monitor_pool import monitor_pool

app = FastAPI(
    title="MemoryTree API",
    description="Memory Tree 服务API",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化服务
workflow_service = WorkflowService()
chat_service = ChatService(workflow_service.workflow_manager)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.post("/chat", response_model=ChatResponse, name="chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """
    处理用户对话
    - 接收用户输入
    - 返回AI响应
    - 可能触发工作流
    """
    try:
        logger.info(f"处理用户输入: {request.user_input[:20]}...")
        result = await chat_service.chat(request.user_input)
        if "unit_id" in result:
            logger.info(f"触发工作流: {result['unit_id']}")
        return ChatResponse(**result)
    except Exception as e:
        logger.error(f"聊天处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/import-dialogue", response_model=ImportDialogueResponse, name="import_dialogue")
async def import_dialogue(request: ImportDialogueRequest) -> ImportDialogueResponse:
    """
    导入历史对话
    - 接收对话历史
    - 触发工作流处理
    """
    try:
        logger.info(f"收到导入请求: {len(request.dialogue_history)} 条对话")
        unit_id = await chat_service.import_dialogue(
            [entry.model_dump() for entry in request.dialogue_history]
        )
        logger.info(f"导入成功，工作单元ID: {unit_id}")
        return ImportDialogueResponse(unit_id=unit_id)
    except Exception as e:
        logger.error(f"导入对话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workflow/{unit_id}/status", response_model=WorkflowStatus)
async def get_workflow_status(unit_id: str) -> WorkflowStatus:
    """获取工作流状态"""
    try:
        logger.info(f"接收状态查询请求: {unit_id}")
        status = await workflow_service.get_workflow_status(unit_id)

        if not status:
            logger.error(f"工作单元不存在或状态获取失败: {unit_id}")
            raise HTTPException(
                status_code=404,
                detail=f"工作单元不存在或状态获取失败: {unit_id}"
            )

        # 验证状态数据
        try:
            workflow_status = WorkflowStatus(**status)
            logger.info(f"返回工作流状态: {workflow_status.status}, ID: {unit_id}")
            return workflow_status
        except ValidationError as e:
            logger.error(f"状态数据验证失败: {str(e)}, 数据: {status}")
            raise HTTPException(
                status_code=500,
                detail=f"状态数据格式错误: {str(e)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工作流状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workflow/{unit_id}/svg", response_model=SVGResult)
async def get_svg_result(unit_id: str) -> SVGResult:
    """获取SVG生成结果"""
    try:
        logger.info(f"获取SVG结果: {unit_id}")
        result = await workflow_service.get_svg_result(unit_id)

        if not result:
            raise HTTPException(
                status_code=404,
                detail="SVG结果不存在或生成失败"
            )

        try:
            return SVGResult(**result)
        except ValidationError as e:
            logger.error(f"SVG数据验证失败: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"SVG数据格式错误: {str(e)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取SVG结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    logger.error(f"未处理的异常: {str(exc)}")
    return {
        "error": str(exc),
        "detail": "服务器内部错误"
    }


@app.get("/monitor/all")
async def get_all_monitor_data():
    """获取所有监控数据"""
    try:
        data = await monitor_pool.get_data()
        # 先试用模拟数据
        # data = await monitor_pool.get_mock_data()
        return data
    except Exception as e:
        logger.error(f"获取监控数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/monitor/{category}")
async def get_category_monitor(category: str):
    """获取特定类别的监控数据"""
    try:
        data = await monitor_pool.get_data(category=category)
        if not data:
            raise HTTPException(status_code=404, detail=f"未找到类别: {category}")
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取监控数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def startup_event():
    """程序启动时的初始化"""
    try:
        # 初始化监控池
        await monitor_pool.initialize()
        logger.info("应用启动完成")
    except Exception as e:
        logger.error(f"应用启动失败: {str(e)}")
        raise
