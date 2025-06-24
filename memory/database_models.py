"""
SQLAlchemy ORM models for the B2BValue application.
"""

import uuid
try:
    import orjson
except ImportError:
    import json
    class orjson:
        @staticmethod
        def dumps(v):
            return json.dumps(v).encode("utf-8")
        @staticmethod
        def loads(v):
            return json.loads(v)
from sqlalchemy import (
    create_engine, Column, String, DateTime, ForeignKey, Integer, JSON, ARRAY, Text, CheckConstraint, TypeDecorator
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

# Custom TypeDecorator for JSON handling, especially for SQLite
class ArrayAsJsonText(TypeDecorator):
    """Represents a Python list as a JSON-encoded string in the DB.

    Stores as TEXT, uses orjson for serialization/deserialization.
    """
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if not isinstance(value, list):
                # Or raise a TypeError, depending on desired strictness
                # For now, let's assume it should be a list or None
                raise ValueError("ArrayAsJsonText expects a list or None")
            return orjson.dumps(value).decode('utf-8')
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            loaded_value = orjson.loads(value)
            if not isinstance(loaded_value, list):
                # Handle cases where DB might store non-list JSON, though unlikely with our bind
                raise ValueError("ArrayAsJsonText expected to deserialize a list")
            return loaded_value
        return value

    def copy(self, **kw): # pragma: no cover
        return ArrayAsJsonText()


class JsonAsText(TypeDecorator):
    """Represents an immutable structure as a json-encoded string in the DB.

    Usage::

        JsonAsText(255)

    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            # Use orjson for efficient serialization
            # Ensure bytes are decoded to string for TEXT column
            return orjson.dumps(value).decode('utf-8')
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return orjson.loads(value)
        return value

    def copy(self, **kw): # pragma: no cover
        # For TypeDecorator, copy() is used by SQLAlchemy internally.
        # If the custom type had parameters (e.g., length for a VARCHAR-like type),
        # they should be passed to the constructor here.
        # Since our JsonAsText is based on TEXT and doesn't take parameters itself,
        # we just return a new instance of JsonAsText.
        return JsonAsText()

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
    entry_metadata = Column(JsonAsText, nullable=False, default={})
    tags = Column(ArrayAsJsonText, nullable=False, default=[]) # Uses ArrayAsJsonText
    version = Column(Integer, nullable=False)
    checksum = Column(String(64))
    access_policy = Column(JsonAsText)

    # WorkflowMemoryEntity Fields
    workflow_id = Column(String(36), nullable=False)
    workflow_name = Column(String(255), nullable=False)
    workflow_status = Column(String(50), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True))
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    customer_id = Column(String(255))
    context_versions = Column(ArrayAsJsonText, nullable=False, default=[]) # Uses ArrayAsJsonText
    stages = Column(JsonAsText, nullable=False, default=[])
    result = Column(JsonAsText)

    user = relationship("User", back_populates="episodic_entries")

    __table_args__ = (CheckConstraint(tier == 'EPISODIC', name='check_tier_is_episodic'),)


class Model(Base):
    __tablename__ = 'models'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    metadata_ = Column(JsonAsText, name='metadata') # Renamed to avoid conflict with Python's metadata

    components = relationship("ModelComponent", back_populates="model", cascade="all, delete-orphan")
    connections = relationship("ModelConnection", back_populates="model", cascade="all, delete-orphan")


class ModelComponent(Base):
    __tablename__ = 'model_components'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4())) # Use String for component ID as it might not be a UUID
    model_id = Column(UUID(as_uuid=True), ForeignKey('models.id', ondelete='CASCADE'), nullable=False)
    type = Column(String, nullable=False)
    properties = Column(JsonAsText, nullable=False)
    position = Column(JsonAsText, nullable=False)
    size = Column(JsonAsText)

    model = relationship("Model", back_populates="components")


class ModelConnection(Base):
    __tablename__ = 'model_connections'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4())) # Use String for connection ID
    model_id = Column(UUID(as_uuid=True), ForeignKey('models.id', ondelete='CASCADE'), nullable=False)
    source = Column(String, nullable=False)
    target = Column(String, nullable=False)
    source_handle = Column(String, name='sourceHandle')
    target_handle = Column(String, name='targetHandle')

    model = relationship("Model", back_populates="connections")
