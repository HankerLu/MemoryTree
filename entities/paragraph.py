from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from database.mysql_connector import Base

class Paragraph(Base):
    __tablename__ = "narrative_paragraphs"
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    narrative_id = Column(Integer, ForeignKey('narratives.id', ondelete='CASCADE'), nullable=False)
    content = Column(Text, nullable=False)
    sequence_number = Column(Integer, nullable=False)
    paragraph_type = Column(String(20), nullable=False)  # 事实描述/情感表达/对话内容/环境描述/思考感悟
    create_time = Column(DateTime, default=datetime.now)
    modified_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联关系
    narrative = relationship("Narrative", back_populates="paragraphs")
    tags = relationship("Tag", secondary="paragraph_tag_associations", back_populates="paragraphs")

    def to_dict(self):
        return {
            'id': self.id,
            'narrative_id': self.narrative_id,
            'content': self.content,
            'sequence_number': self.sequence_number,
            'paragraph_type': self.paragraph_type,
            'create_time': self.create_time,
            'modified_time': self.modified_time
        } 