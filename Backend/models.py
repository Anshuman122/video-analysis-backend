from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from .database import Base

class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(Integer, primary_key=True, index=True)
    video_url = Column(String, index=True)
    status = Column(String, default="processing")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    result = Column(Text, nullable=True)