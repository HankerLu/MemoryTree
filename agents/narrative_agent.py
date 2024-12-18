import zhipuai
import os
from dotenv import load_dotenv

load_dotenv()

class NarrativeAgent:
    def __init__(self):
        self.api_key = os.getenv("API_KEY_CONF")
        zhipuai.api_key = self.api_key
        self.client = zhipuai.ZhipuAI(api_key=self.api_key)
        
    def generate_narrative(self, conversation_history):
        """将对话历史转换为叙事体"""
        # 过滤掉系统消息，只保留用户和助手的对话
        dialogue = [msg for msg in conversation_history if msg["role"] != "system"]
        
        prompt = f"""请将以下对话转换成一篇流畅的第一人称回忆录叙事体。要求：
1. 以自然的叙事方式展现对话内容
2. 保留对话中的关键信息和情感
3. 使用适当的过渡词连接各个部分
4. 注意时间和情节的连贯性

对话内容：
{self._format_conversation(dialogue)}"""
        
        try:
            response = self.client.chat.completions.create(
                model="glm-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            
            return response.choices[0].message.content
                
        except Exception as e:
            return f"生成叙事体时发生错误：{str(e)}"
    
    def _format_conversation(self, conversation_history):
        """格式化对话历史"""
        formatted = []
        for msg in conversation_history:
            role = "我" if msg["role"] == "user" else "采访者"
            formatted.append(f"{role}：{msg['content']}")
        return "\n".join(formatted) 