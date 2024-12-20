from typing import Optional, List
from sqlalchemy import select
from entities.tag import Tag
from database.base import get_db

class TagService:
    def __init__(self):
        self._session = None

    def create(self, tag: Tag) -> Tag:
        """创建标签"""
        if self._session:
            self._session.add(tag)
            self._session.flush()
            return tag
            
        with get_db() as db:
            db.add(tag)
            db.flush()
            return tag

    def get_by_id(self, tag_id: int) -> Optional[Tag]:
        """根据ID获取标签"""
        if self._session:
            return self._session.get(Tag, tag_id)
            
        with get_db() as db:
            return db.get(Tag, tag_id)

    def get_by_dimension(self, dimension: str) -> List[Tag]:
        """获取指定维度的所有标签"""
        stmt = select(Tag).where(Tag.dimension == dimension)
        if self._session:
            return list(self._session.scalars(stmt))
            
        with get_db() as db:
            return list(db.scalars(stmt))

    def update(self, tag: Tag) -> Tag:
        """更新标签"""
        if self._session:
            self._session.merge(tag)
            return tag
            
        with get_db() as db:
            db.merge(tag)
            return tag

    def delete(self, tag_id: int) -> bool:
        """删除标签"""
        if self._session:
            tag = self._session.get(Tag, tag_id)
            if tag:
                # 先清除关联关系
                tag.paragraphs = []
                self._session.delete(tag)
                self._session.flush()
                return True
            return False
            
        with get_db() as db:
            tag = db.get(Tag, tag_id)
            if tag:
                # 先清除关联关系
                tag.paragraphs = []
                db.delete(tag)
                return True
            return False

    def get_by_paragraph(self, paragraph_id: int) -> List[Tag]:
        """获取段落的所有标签"""
        stmt = select(Tag).join(Tag.paragraphs)\
                         .where(Tag.paragraphs.any(id=paragraph_id))
        if self._session:
            return list(self._session.scalars(stmt))
            
        with get_db() as db:
            return list(db.scalars(stmt))

    def find_by_dimension_and_value(self, dimension: str, value: str) -> Optional[Tag]:
        """根据维度和值查找标签"""
        stmt = select(Tag).where(
            Tag.dimension == dimension,
            Tag.tag_value == value
        )
        
        if self._session:
            return self._session.scalar(stmt)
            
        with get_db() as db:
            return db.scalar(stmt) 