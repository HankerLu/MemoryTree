from typing import Optional
from sqlalchemy import select
from entities.narrative import Narrative
from database.base import get_db

class NarrativeService:
    def __init__(self):
        self._session = None

    def create(self, narrative: Narrative) -> Narrative:
        """创建叙事体"""
        if self._session:
            self._session.add(narrative)
            self._session.flush()
            return narrative
            
        with get_db() as db:
            db.add(narrative)
            db.flush()
            return narrative

    def get_by_id(self, narrative_id: int) -> Optional[Narrative]:
        """根据ID获取叙事体"""
        if self._session:
            return self._session.get(Narrative, narrative_id)
            
        with get_db() as db:
            return db.get(Narrative, narrative_id)

    def get_by_session(self, session_id: str) -> Optional[Narrative]:
        """根据会话ID获取叙事体"""
        stmt = select(Narrative).where(Narrative.session_id == session_id)
        if self._session:
            return self._session.scalar(stmt)
            
        with get_db() as db:
            return db.scalar(stmt)

    def update(self, narrative: Narrative) -> Narrative:
        """更新叙事体"""
        if self._session:
            self._session.merge(narrative)
            return narrative
            
        with get_db() as db:
            db.merge(narrative)
            return narrative

    def delete(self, narrative_id: int) -> bool:
        """删除叙事体"""
        if self._session:
            narrative = self._session.get(Narrative, narrative_id)
            if narrative:
                self._session.delete(narrative)
                return True
            return False
            
        with get_db() as db:
            narrative = db.get(Narrative, narrative_id)
            if narrative:
                db.delete(narrative)
                return True
            return False 