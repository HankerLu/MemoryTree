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
        try:
            # 过滤掉系统消息，只保留用户和助手的对话
            dialogue = [msg for msg in conversation_history if msg["role"] != "system"]
            
            if not dialogue:
                return "对话历史中没有有效的对话内容"
            
            prompt = f"""请将以下对话内容转换成一篇流畅的第一人称回忆录叙事体。要求：
1. 只关注对话中"user"（讲述者）所分享的经历和故事内容
2. 以讲述者的第一人称视角展开叙述
3. 忽略采访者的提问和回应，仅将其作为引出故事的线索
4. 将零散的对话内容重新组织成连贯的叙事
5. 保持原有故事的情感基调和关键细节
6. 使用优美流畅的文学语言

对话内容：
{self._format_conversation(dialogue)}"""
            
            try:
                response = self.client.chat.completions.create(
                    model="glm-4-air",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                )
                
                return response.choices[0].message.content
                    
            except Exception as e:
                return f"调用AI接口时发生错误：{str(e)}"
                
        except Exception as e:
            return f"处理对话历史时发生错误：{str(e)}"
    
    def _format_conversation(self, conversation_history):
        """格式化对话历史"""
        formatted = []
        for msg in conversation_history:
            role = "讲述者" if msg["role"] == "user" else "采访者"
            formatted.append(f"{role}：{msg['content']}")
        return "\n".join(formatted) 