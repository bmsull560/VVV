"""
SQLAlchemy ORM models for the B2BValue application.
"""

import uuid
from sqlalchemy import (
    create_engine, Column, String, DateTime, ForeignKey, Integer, JSON, ARRAY, Text, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    episodic_entries = relationship("EpisodicMemoryEntry", back_populates="user")

class EpisodicMemoryEntry(Base):
    __tablename__ = 'episodic_memory_entries'

    # Base MemoryEntity Fields
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    creator_id = Column(String(255), nullable=False)
    sensitivity = Column(String(50), nullable=False)
    tier = Column(String(50), nullable=False)
    ttl = Column(Integer)
    entry_metadata = Column(JSON, nullable=False, default={})
    tags = Column(ARRAY(Text), nullable=False, default=[])
    version = Column(Integer, nullable=False)
    checksum = Column(String(64))
    access_policy = Column(JSON)

    # WorkflowMemoryEntity Fields
    workflow_id = Column(String(36), nullable=False)
    workflow_name = Column(String(255), nullable=False)
    workflow_status = Column(String(50), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True))
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    customer_id = Column(String(255))
    context_versions = Column(ARRAY(Text), nullable=False, default=[])
    stages = Column(JSON, nullable=False, default=[])
    result = Column(JSON)

    user = relationship("User", back_populates="episodic_entries")

    __table_args__ = (CheckConstraint(tier == 'EPISODIC', name='check_tier_is_episodic'),)
