from sqlalchemy import Column, DateTime, Integer, String
from .database import Base


class FileShare(Base):
    __tablename__ = "file_shares"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(64), unique=True, index=True, nullable=False)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(100), nullable=False)
    content_type = Column(String(150), nullable=True)
    file_size = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
