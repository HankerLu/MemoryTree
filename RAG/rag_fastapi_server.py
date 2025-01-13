from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from zhipuai import ZhipuAI
import chromadb
from chromadb.config import Settings
import uvicorn
import json

app = FastAPI(title="RAG Search API")

# 添加 CORS 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,  # 允许携带凭证
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头部
)

# 初始化智谱AI客户端
client_GM = ZhipuAI(api_key="9a9c269a4914924d102c116e2e5e1977.aTo5260Pgma7epzh")


# ... 保持原有的辅助函数不变 ...
def get_embeddings(texts, model="embedding-3"):
    '''封装智谱AI的Embedding接口'''
    data = client_GM.embeddings.create(input=texts, model=model).data
    return [x.embedding for x in data]


def process_conversation_file(file_path):
    '''处理对话文件，提取对话内容'''
    conversations = []
    current_conversation = ""

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if line:
            current_conversation += line + "\n"
        elif current_conversation:
            conversations.append(current_conversation.strip())
            current_conversation = ""

    if current_conversation:
        conversations.append(current_conversation.strip())

    return conversations


class VectorDBService:
    def __init__(self, collection_name="conversation_store"):
        # 初始化ChromaDB客户端
        chroma_client = chromadb.Client(Settings(allow_reset=True))
        self.collection = chroma_client.get_or_create_collection(name=collection_name)

    def add_documents(self, documents):
        '''向数据库添加文档'''
        self.collection.add(
            embeddings=get_embeddings(documents),
            documents=documents,
            ids=[f"id{i}" for i in range(len(documents))]
        )

    def search(self, query, top_n=2):
        '''检索相似文档'''
        results = self.collection.query(
            query_embeddings=get_embeddings([query]),
            n_results=top_n
        )
        return results['documents'][0]


# 创建服务实例
search_service = None


# 定义请求和响应模型
class SearchQuery(BaseModel):
    query: str
    top_n: int = 2


class SearchResponse(BaseModel):
    results: List[str]


@app.on_event("startup")
async def startup_event():
    """在应用启动时初始化向量数据库"""
    global search_service
    try:
        # 创建向量数据库服务
        search_service = VectorDBService()

        # 处理对话文件
        conversations = process_conversation_file("问答.txt")

        # 将对话内容添加到向量数据库
        search_service.add_documents(conversations)

    except Exception as e:
        print(f"初始化失败: {str(e)}")
        raise


@app.get("/")
async def root():
    """API根路径"""
    return {"message": "欢迎使用RAG检索服务"}


@app.post("/search", response_model=SearchResponse)
async def search(query: SearchQuery):
    """
    检索接口

    - query: 查询字符串
    - top_n: 返回结果数量
    """
    if not search_service:
        raise HTTPException(status_code=500, detail="服务未正确初始化")

    try:
        results = search_service.search(query.query, query.top_n)
        return SearchResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 添加 WebSocket 端点
@app.websocket("/ws/search")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()

            try:
                # 解析JSON数据
                query_data = json.loads(data)
                query = query_data.get("query", "")
                top_n = query_data.get("top_n", 2)

                # 执行搜索
                results = search_service.search(query, top_n)

                # 返回结果
                await websocket.send_json({"results": results})

            except json.JSONDecodeError:
                await websocket.send_json({"error": "无效的JSON格式"})
            except Exception as e:
                await websocket.send_json({"error": str(e)})

    except Exception as e:
        print(f"WebSocket错误: {str(e)}")


# 启动服务器的代码
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
