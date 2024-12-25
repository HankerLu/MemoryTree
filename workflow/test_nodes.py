import asyncio
from typing import Dict, Any

async def mock_conversation_process(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """模拟对话处理"""
    await asyncio.sleep(2)  # 模拟处理时间
    return {
        "conversation_result": {
            "response": "这是一个测试回应",
            "status": "success"
        },
        "conversation_history": [
            {"role": "user", "content": input_data["user_input"]},
            {"role": "assistant", "content": "这是一个测试回应"}
        ]
    }

async def mock_narrative_process(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """模拟叙事体生成"""
    await asyncio.sleep(3)  # 模拟处理时间
    return {
        "narrative_content": "这是生成的叙事体内容...",
        "narrative_metadata": {
            "word_count": 100,
            "time_period": "童年"
        }
    }

async def mock_analysis_process(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """模拟分析处理"""
    await asyncio.sleep(2)  # 模拟处理时间
    return {
        "analysis_result": {
            "sentence_analysis": {
                "paragraphs": [
                    {"content": "段落1", "type": "叙述"},
                    {"content": "段落2", "type": "对话"}
                ],
                "summary": "段落分析结果"
            },
            "tag_analysis": {
                "tags": {
                    "time_tags": ["童年", "小学"],
                    "emotion_tags": ["快乐", "怀念"]
                },
                "summary": "标签分析结果"
            }
        },
        "paragraphs": [
            {"content": "段落1", "type": "叙述"},
            {"content": "段落2", "type": "对话"}
        ],
        "tags": {
            "time_tags": ["童年", "小学"],
            "emotion_tags": ["快乐", "怀念"]
        }
    }

async def mock_svg_process(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """模拟SVG生成"""
    await asyncio.sleep(1)  # 模拟处理时间
    return {
        "svg_content": "<svg>测试SVG内容</svg>"
    } 