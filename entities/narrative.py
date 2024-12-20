from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from database.mysql_connector import Base

class Narrative(Base):
    __tablename__ = "narratives"
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    create_time = Column(DateTime, default=datetime.now)
    modified_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    paragraphs = relationship("Paragraph", back_populates="narrative", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'content': self.content,
            'create_time': self.create_time,
            'modified_time': self.modified_time
        } 