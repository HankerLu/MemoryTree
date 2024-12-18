import zhipuai
import os
from dotenv import load_dotenv

load_dotenv()

class NarrativeAgent:
    def __init__(self):
        self.api_key = os.getenv("e64b996267bee6ba0252a5d46a143ff4.3RZ8v4qZ2DbYoJbk")
        zhipuai.api_key = self.api_key
        
    def generate_narrative(self, conversation_history):
        """将对话历史转换为叙事体"""
        prompt = f"""请将以下对话历史转换成回忆录叙事体，以第一人称的视角描述这段对话经历：

对话历史：
{self._format_conversation(conversation_history)}

请生成一段流畅的叙事体，包含对话的关键信息和情感表达。"""
        
        try:
            response = zhipuai.model_api.invoke(
                model="chatglm_turbo",
                prompt=[{"role": "user", "content": prompt}],
                temperature=0.8,
            )
            
            if response.get("code") == 200:
                return response["data"]["choices"][0]["content"]
            else:
                return f"错误：{response.get('msg', '未知错误')}"
                
        except Exception as e:
            return f"发生���误：{str(e)}"
    
    def _format_conversation(self, conversation_history):
        """格式化对话历史"""
        formatted = []
        for msg in conversation_history:
            role = "用户" if msg["role"] == "user" else "助手"
            formatted.append(f"{role}：{msg['content']}")
        return "\n".join(formatted) 