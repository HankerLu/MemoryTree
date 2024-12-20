from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from database.base import Base

class Dialogue(Base):
    __tablename__ = "dialogue_history"
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), nullable=False)
    role = Column(String(20), nullable=False)  # user/assistant
    content = Column(Text, nullable=False)
    sequence_number = Column(Integer, nullable=False)
    create_time = Column(DateTime, default=datetime.now)
    modified_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<Dialogue(id={self.id}, session_id={self.session_id})>"

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'role': self.role,
            'content': self.content,
            'sequence_number': self.sequence_number,
            'create_time': self.create_time,
            'modified_time': self.modified_time
        } 