from typing import List, Optional
from datetime import datetime
from entities.dialogue import Dialogue
from database.base import get_db

class ConversationService:
    def __init__(self):
        self._session = None
        
    def save_history(self, session_id: str, history: list) -> bool:
        """保存对话历史"""
        try:
            dialogues = []
            for idx, msg in enumerate(history, 1):
                dialogue = Dialogue(
                    session_id=session_id,
                    role=msg.get('role'),
                    content=msg.get('content'),
                    sequence_number=idx
                )
                dialogues.append(dialogue)
                
            if self._session:
                for d in dialogues:
                    self._session.add(d)
                self._session.flush()
                return True
                
            with get_db() as db:
                for d in dialogues:
                    db.add(d)
                return True
                
        except Exception as e:
            print(f"保存对话历史时发生错误: {str(e)}")
            return False 