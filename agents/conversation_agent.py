import zhipuai
import os
from dotenv import load_dotenv

load_dotenv()

class ConversationAgent:
    def __init__(self):
        self.api_key = os.getenv("e64b996267bee6ba0252a5d46a143ff4.3RZ8v4qZ2DbYoJbk")
        zhipuai.api_key = self.api_key
        self.conversation_history = []
        
    def chat(self, user_input):
        """与用户进行对话"""
        self.conversation_history.append({"role": "user", "content": user_input})
        
        try:
            response = zhipuai.model_api.invoke(
                model="chatglm_turbo",
                prompt=self.conversation_history,
                temperature=0.7,
            )
            
            if response.get("code") == 200:
                assistant_response = response["data"]["choices"][0]["content"]
                self.conversation_history.append({"role": "assistant", "content": assistant_response})
                return assistant_response
            else:
                return f"错误：{response.get('msg', '未知错误')}"
                
        except Exception as e:
            return f"发生错误：{str(e)}"
    
    def get_conversation_history(self):
        """获取对话历史"""
        return self.conversation_history
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = [] 