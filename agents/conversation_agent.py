import zhipuai
import os
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

class ConversationAgent:
    def __init__(self):
        self.api_key = os.getenv("API_KEY_CONF")
        print(f"Debug - API密钥: {self.api_key}")  # 仅用于调试
        if not self.api_key:
            raise ValueError("未找到API密钥，请检查环境变量 API_KEY_CONF")
        self.client = zhipuai.ZhipuAI(api_key=self.api_key)
        self.conversation_history = []
        self.init_conversation_history()
        # 创建日志文件
        self.create_new_log_file()
        self.save_history()

    def create_new_log_file(self):
        """创建新的日志文件"""
        os.makedirs('logs', exist_ok=True)
        self.log_file = f"logs/conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    def init_conversation_history(self):
        """初始化对话历史"""
        prompt_template = """你是一位专业的回忆录采访者。你的任务是通过对话的方式，引导用户回忆和分享他们人生中的重要经历、情感和故事。

请遵循以下原则：
1. 以温和友善的态度与用户交谈，营造轻松舒适的氛围
2. 循序渐进地引导用户展开回忆，从简单的话题逐渐深入
3. 针对用户提到的关键事件、人物或情感进行追问，获取更丰富的细节
4. 适时给予共情回应，鼓励用户表达真实的想法和感受
5. 注意保护用户隐私，对敏感话题保持谨慎

你的目标是帮助用户梳理生命历程中的重要片段，收集有价值的回忆素材，为创作一部完整的回忆录做准备。"""
        messages=[
            {"role": "system", "content": prompt_template}
        ]
        self.conversation_history = messages
        
    def save_history(self):
        """保存对话历史到日志文件"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存对话历史时发生错误：{str(e)}")

    def set_conversation_history(self, history):
        """设置当前对话历史
        
        Args:
            history (list): 要设置的对话历史列表，每个元素应该是包含 role 和 content 的字典
            
        Returns:
            bool: 设置是否成功
            
        Raises:
            ValueError: 当输入的历史记录格式不正确时抛出
        """
        try:
            # 验证输入格式
            if not isinstance(history, list):
                raise ValueError("对话历史必须是列表格式")
                
            for message in history:
                if not isinstance(message, dict):
                    raise ValueError("对话历史中的每条消息必须是字典格式")
                if 'role' not in message or 'content' not in message:
                    raise ValueError("每条消息必须包含 'role' 和 'content' 字段")
                if message['role'] not in ['system', 'user', 'assistant']:
                    raise ValueError("消息角色必须是 'system'、'user' 或 'assistant'")
            
            # 设置新的对话历史
            self.conversation_history = history
            
            # 保存到新的日志文件
            self.create_new_log_file()
            self.save_history()
            
            return True
            
        except Exception as e:
            print(f"设置对话历史时发生错误：{str(e)}")
            return False


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
            self.save_history()  # 每次对话后保存历史
            return assistant_response
                
        except Exception as e:
            print(f"发生错误：{str(e)}")
            return f"发生错误：{str(e)}"
    
    def get_conversation_history(self):
        """获取当前会话的对话历史"""

        return self.conversation_history
    
    def clear_history(self):
        """清空对话历史"""
        # 创建新的日志文件
        self.create_new_log_file()
        # 重新初始化对话历史，保留系统提示
        self.init_conversation_history()
        # 保存清空后的历史到新文件
        self.save_history()

