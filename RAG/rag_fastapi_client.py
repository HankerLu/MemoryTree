import asyncio
import websockets
import json
import sys
from websockets.exceptions import ConnectionClosedError


async def rag_client():
    uri = "ws://localhost:8000/ws/search"

    while True:
        try:
            async with websockets.connect(uri) as websocket:
                print("已连接到服务器")

                while True:
                    try:
                        # 获取用户输入
                        query = input("\n请输入查询内容 (输入'quit'退出): ")
                        if query.lower() == 'quit':
                            return

                        try:
                            top_n = int(input("请输入需要返回的结果数量 (1-5): "))
                            if top_n < 1 or top_n > 5:
                                print("结果数量必须在1-5之间")
                                continue
                        except ValueError:
                            print("请输入有效的数字")
                            continue

                        # 发送查询
                        message = {
                            "query": query,
                            "top_n": top_n
                        }
                        await websocket.send(json.dumps(message))

                        # 接收响应
                        response = await websocket.recv()
                        try:
                            response_data = json.loads(response)
                            if "error" in response_data:
                                print(f"\n错误：{response_data['error']}")
                            else:
                                print("\n查询结果：")
                                for idx, result in enumerate(response_data['results'], 1):
                                    print(f"{idx}. {result}")
                        except json.JSONDecodeError:
                            print(f"\n收到无效响应：{response}")

                    except ConnectionClosedError:
                        print("\n连接已断开，正在尝试重新连接...")
                        break
                    except Exception as e:
                        print(f"\n发生错误：{str(e)}")
                        break

        except ConnectionRefusedError:
            print("\n无法连接到服务器，请确保服务器正在运行")
            retry = input("是否重试连接？(y/n): ")
            if retry.lower() != 'y':
                return
        except Exception as e:
            print(f"\n发生错误：{str(e)}")
            retry = input("是否重试连接？(y/n): ")
            if retry.lower() != 'y':
                return

        # 等待一段时间后重试
        await asyncio.sleep(2)


def main():
    try:
        asyncio.run(rag_client())
    except KeyboardInterrupt:
        print("\n程序已终止")
    except Exception as e:
        print(f"\n程序异常退出：{str(e)}")
    finally:
        print("\n感谢使用！")


if __name__ == "__main__":
    main()