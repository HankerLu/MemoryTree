import zhipuai
import os
from dotenv import load_dotenv

load_dotenv()

class NarrativeAgent:
    def __init__(self):
        self.api_key = os.getenv("API_KEY_CONF")
        zhipuai.api_key = self.api_key
        
    def generate_narrative(self, conversation_history):
        """将对话历史转换为叙事体"""
        prompt = f"""请将以下对话历史转换成回忆录叙事体，以第一人称的视角描述这段对话经历：

对话历史：
{self._format_conversation(conversation_history)}

请生成一段流畅的叙事体，包含对话的关键信息和情感表达。"""
        
        try:
            response = zhipuai.ZhipuAI().chat.completions.create(
                model="chatglm_turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
            )
            
            return response.choices[0].message.content
                
        except Exception as e:
            return f"发生错误：{str(e)}"
    
    def _format_conversation(self, conversation_history):
        """格式化对话历史"""
        formatted = []
        for msg in conversation_history:
            role = "用户" if msg["role"] == "user" else "助手"
            formatted.append(f"{role}：{msg['content']}")
        return "\n".join(formatted) 