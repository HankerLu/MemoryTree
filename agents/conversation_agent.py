import zhipuai
import os
from dotenv import load_dotenv

load_dotenv()

class ConversationAgent:
    def __init__(self):
        self.api_key = os.getenv("API_KEY_CONF")
        print(f"Debug - API密钥: {self.api_key}")  # 仅用于调试
        if not self.api_key:
            raise ValueError("未找到API密钥，请检查环境变量 API_KEY_CONF")
        self.client = zhipuai.ZhipuAI(api_key=self.api_key)
        self.conversation_history = []
        
    def chat(self, user_input):
        """与用户进行对话"""
        self.conversation_history.append({"role": "user", "content": user_input})
        
        try:
            response = self.client.chat.completions.create(
                model="glm-4",
                messages=self.conversation_history,
                temperature=0.7,
            )
            
            assistant_response = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": assistant_response})
            return assistant_response
                
        except Exception as e:
            print(f"发生错误：{str(e)}")
            return f"发生错误：{str(e)}"
    
    def get_conversation_history(self):
        """获取对话历史"""
        return self.conversation_history
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = [] 