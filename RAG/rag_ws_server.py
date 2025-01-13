import asyncio
import websockets
import json
from zhipuai import ZhipuAI
import chromadb
from chromadb.config import Settings


# 初始化智谱AI客户端
client_GM = ZhipuAI(api_key="9a9c269a4914924d102c116e2e5e1977.aTo5260Pgma7epzh")

# 创建服务实例
search_service = None

def get_embeddings(texts, model="embedding-3"):
    '''封装智谱AI的Embedding接口'''
    data = client_GM.embeddings.create(input=texts, model=model).data
    return [x.embedding for x in data]

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

def init_service():
    """初始化向量数据库服务"""
    global search_service
    try:
        # 创建向量数据库服务
        search_service = VectorDBService()

        # 处理对话文件
        with open("问答.txt", 'r', encoding='utf-8') as f:
            lines = f.readlines()

        conversations = []
        current_conversation = ""
        for line in lines:
            line = line.strip()
            if line:
                current_conversation += line + "\n"
            elif current_conversation:
                conversations.append(current_conversation.strip())
                current_conversation = ""

        if current_conversation:
            conversations.append(current_conversation.strip())

        # 将对话内容添加到向量数据库
        search_service.add_documents(conversations)
        print("向量数据库初始化成功")

    except Exception as e:
        print(f"初始化失败: {str(e)}")
        raise


async def handle_websocket(websocket):
    """处理WebSocket连接"""
    client_id = id(websocket)
    remote_address = websocket.remote_address if hasattr(websocket, 'remote_address') else 'unknown'
    print(f"新客户端连接: {client_id}")
    print(f"客户端地址: {remote_address}")

    try:
        async for message in websocket:
            try:
                print(f"收到消息: {message}")

                # 解析JSON数据
                data = json.loads(message)
                query = data.get("query", "")
                top_n = data.get("top_n", 2)

                if not query:
                    await websocket.send(json.dumps({"error": "查询内容不能为空"}))
                    continue

                # 执行搜索
                results = search_service.search(query, top_n)

                # 发送响应
                response = {"results": results}
                await websocket.send(json.dumps(response))
                print(f"已发送响应到客户端 {client_id}")

            except json.JSONDecodeError as e:
                print(f"JSON解析错误: {str(e)}")
                await websocket.send(json.dumps({"error": "无效的JSON格式"}))
            except Exception as e:
                print(f"处理消息时出错: {str(e)}")
                await websocket.send(json.dumps({"error": str(e)}))

    except websockets.exceptions.ConnectionClosed as e:
        print(f"客户端 {client_id} 断开连接: {str(e)}")
    except Exception as e:
        print(f"处理客户端 {client_id} 时发生错误: {str(e)}")
    finally:
        print(f"客户端 {client_id} 连接已关闭")


async def main():
    # 初始化服务
    init_service()

    # 启动WebSocket服务器
    async with websockets.serve(
            handle_websocket,  # 使用路由函数替代直接的处理函数
            "0.0.0.0",
            8000,
            ping_interval=20,
            ping_timeout=60,
            max_size=10485760
    ) as server:
        print("WebSocket服务器已启动，监听 ws://0.0.0.0:8000")
        await asyncio.Future()  # 永久运行


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"服务器发生错误: {str(e)}")