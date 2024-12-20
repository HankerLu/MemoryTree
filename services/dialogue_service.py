from typing import Optional, List
from sqlalchemy import select
from entities.dialogue import Dialogue
from database.base import get_db

class DialogueService:
    def __init__(self):
        self._session = None

    def create(self, dialogue: Dialogue) -> Dialogue:
        """创建对话记录"""
        if self._session:
            # 使用注入的会话
            self._session.flush()  # 确保获取ID
            return dialogue
        
        with get_db() as db:
            db.add(dialogue)
            db.flush()
            return dialogue

    def get_by_id(self, dialogue_id: int) -> Optional[Dialogue]:
        """根据ID获取对话记录"""
        if self._session:
            return self._session.get(Dialogue, dialogue_id)
            
        with get_db() as db:
            return db.get(Dialogue, dialogue_id)

    def get_by_session(self, session_id: str) -> List[Dialogue]:
        """获取会话的所有对话记录"""
        stmt = select(Dialogue).where(Dialogue.session_id == session_id)\
                             .order_by(Dialogue.sequence_number)
        if self._session:
            return list(self._session.scalars(stmt))
            
        with get_db() as db:
            return list(db.scalars(stmt))

    def update(self, dialogue: Dialogue) -> Dialogue:
        """更新对话记录"""
        if self._session:
            self._session.merge(dialogue)
            return dialogue
            
        with get_db() as db:
            db.merge(dialogue)
            return dialogue

    def delete(self, dialogue_id: int) -> bool:
        """删除对话记录"""
        if self._session:
            dialogue = self._session.get(Dialogue, dialogue_id)
            if dialogue:
                self._session.delete(dialogue)
                return True
            return False
            
        with get_db() as db:
            dialogue = db.get(Dialogue, dialogue_id)
            if dialogue:
                db.delete(dialogue)
                return True
            return False