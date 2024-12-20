from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from database.mysql_connector import Base

# 创建关联表
paragraph_tag_association = Table(
    'paragraph_tag_associations',
    Base.metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('paragraph_id', Integer, ForeignKey('narrative_paragraphs.id', ondelete='CASCADE')),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE')),
    Column('create_time', DateTime, default=datetime.now),
    Column('modified_time', DateTime, default=datetime.now, onupdate=datetime.now)
)

class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    dimension = Column(String(20), nullable=False)  # 时间维度/场景维度/情感维度/事件维度/人物维度
    tag_value = Column(String(50), nullable=False)
    create_time = Column(DateTime, default=datetime.now)
    modified_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联关系
    paragraphs = relationship("Paragraph", secondary=paragraph_tag_association, back_populates="tags")

    def to_dict(self):
        return {
            'id': self.id,
            'dimension': self.dimension,
            'tag_value': self.tag_value,
            'create_time': self.create_time,
            'modified_time': self.modified_time
        } 