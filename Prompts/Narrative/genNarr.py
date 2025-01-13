import requests
import json
from typing import List, Dict


class OllamaAPI:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url

    def generate(self, prompt, model="qwen2.5:1.5b", **kwargs):
        """
        向Ollama发送生成请求
        """
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }

        # 添加可选参数
        valid_params = {
            "temperature",
            "top_p",
            "top_k",
            "repeat_penalty",
            "seed",
            "num_predict",
            "stop"
        }

        # 只添加有效的参数
        for key, value in kwargs.items():
            if key in valid_params:
                payload[key] = value

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"请求出错: {e}")
            return None


def read_conversation_history(file_path: str) -> List[Dict]:
    """
    读取对话历史文件
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取文件出错: {e}")
        return []


def generate_memoir(conversation_history: List[Dict]) -> str:
    """
    生成回忆录提示词
    """
    prompt = f"""请将以下对话内容转换成一篇流畅的第一人称回忆录叙事体。要求：
1. 仅围绕对话中"user"（讲述者）所分享的经历和故事内容展开。
2. 以讲述者的第一人称视角进行叙述，不得添加未在对话中出现的内容。
3. 完全忽略采访者的提问和回应，仅将其作为引出故事的线索。
4. 把零散的对话内容精心组织成连贯的叙事，同时严格保留原有故事的情感基调和关键细节，不得擅自添加情感色彩或虚构细节。
5. 使用优美流畅的文学语言进行表达。
对话内容：
{json.dumps(conversation_history, ensure_ascii=False, indent=2)}"""
    return prompt


def main():
    # 创建API实例
    ollama = OllamaAPI()

    # 读取对话历史
    conversation_file = "../../logs/test.json"
    conversation_history = read_conversation_history(conversation_file)

    if not conversation_history:
        print("无法读取对话历史")
        return

    # 生成提示词
    prompt = generate_memoir(conversation_history)

    # 设置生成参数
    generation_params = {
        "temperature": 0.5,  # 控制创造性，值越高越创造性
    }

    # 调用模型生成回忆录
    response = ollama.generate(
        prompt=prompt,
        model="qwen2.5:7b",
        **generation_params
    )

    if response:
        print("\n生成的回忆录内容:")
        print("-" * 50)
        print(response.get('response', '无响应'))
        print("-" * 50)


if __name__ == "__main__":
    main()