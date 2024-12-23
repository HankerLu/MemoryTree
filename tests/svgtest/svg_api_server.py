from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, project_root)

from services.book_svg_service import BookSVGService

app = FastAPI(
    title="Book SVG Generator API",
    description="用于生成书籍SVG页面的API服务",
    version="1.0.0"
)

# 请求模型
class PageRequest(BaseModel):
    number: str = "Chapter 1"  # 章节号或节号，如 "Chapter 1" 或 "第1节"
    title: str = "标题"       # 章节标题或节标题
    content: Optional[str] = None  # 正文内容，章节页面可为空
    is_chapter: bool = False  # 是否为章节页面
    
    class Config:
        json_schema_extra = {
            "example": {
                "number": "第3节",
                "title": "家里祭拜",
                "content": "从小，我就对篮球充满了热情。无论是在学校的操场上...",
                "is_chapter": False
            }
        }

# 响应模型
class PageResponse(BaseModel):
    pages: List[str]  # SVG页面列表
    page_count: int   # 页面总数

@app.post("/generate/svg", response_model=PageResponse)
async def generate_svg(request: PageRequest):
    """
    生成SVG页面
    
    参数说明:
    - number: 章节号或节号，如 "Chapter 1" 或 "第1节"
    - title: 章节标题或节标题
    - content: 正文内容（章节页面可为空）
    - is_chapter: 是否为章节页面（true/false）
    """
    try:
        service = BookSVGService()
        pages = service.generate_svg(
            number=request.number,
            title=request.title,
            content=request.content,
            is_chapter=request.is_chapter
        )
        
        return PageResponse(
            pages=pages,
            page_count=len(pages)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test")
async def test():
    """测试API是否正常运行"""
    return {"message": "API is running"}

if __name__ == "__main__":
    print("Starting SVG Generator API server...")
    print("API documentation available at: http://localhost:8000/docs")
    print("Test endpoint: http://localhost:8000/test")
    uvicorn.run(app, host="0.0.0.0", port=8000) 