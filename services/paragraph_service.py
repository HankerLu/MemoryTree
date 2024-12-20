from typing import Optional, List
from sqlalchemy import select
from entities.paragraph import Paragraph
from database.base import get_db

class ParagraphService:
    def __init__(self):
        self._session = None

    def create(self, paragraph: Paragraph) -> Paragraph:
        """创建段落"""
        if self._session:
            self._session.add(paragraph)
            self._session.flush()
            return paragraph
            
        with get_db() as db:
            db.add(paragraph)
            db.flush()
            return paragraph

    def get_by_id(self, paragraph_id: int) -> Optional[Paragraph]:
        """根据ID获取段落"""
        if self._session:
            return self._session.get(Paragraph, paragraph_id)
            
        with get_db() as db:
            return db.get(Paragraph, paragraph_id)

    def get_by_narrative(self, narrative_id: int) -> List[Paragraph]:
        """获取叙事体的所有段落"""
        stmt = select(Paragraph).where(Paragraph.narrative_id == narrative_id)\
                              .order_by(Paragraph.sequence_number)
        if self._session:
            return list(self._session.scalars(stmt))
            
        with get_db() as db:
            return list(db.scalars(stmt))

    def update(self, paragraph: Paragraph) -> Paragraph:
        """更新段落"""
        if self._session:
            self._session.merge(paragraph)
            return paragraph
            
        with get_db() as db:
            db.merge(paragraph)
            return paragraph

    def delete(self, paragraph_id: int) -> bool:
        """删除段落"""
        if self._session:
            paragraph = self._session.get(Paragraph, paragraph_id)
            if paragraph:
                self._session.delete(paragraph)
                return True
            return False
            
        with get_db() as db:
            paragraph = db.get(Paragraph, paragraph_id)
            if paragraph:
                db.delete(paragraph)
                return True
            return False

    def get_by_type(self, paragraph_type: str) -> List[Paragraph]:
        """根据段落类型获取段落"""
        stmt = select(Paragraph).where(Paragraph.paragraph_type == paragraph_type)
        if self._session:
            return list(self._session.scalars(stmt))
            
        with get_db() as db:
            return list(db.scalars(stmt)) 