"""SQLAlchemy ORM models for diagnostics and sessions."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, Text, DateTime, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="analyst", nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class DiagnosticSession(Base):
    __tablename__ = "diagnostic_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    browser_session_id = Column(String(255), nullable=True)
    tenant_url = Column(String(500), nullable=False)
    module = Column(String(100), nullable=False)  # subscription, order, orchestration
    transaction_ref = Column(String(255), nullable=True)
    status = Column(String(50), default="running")  # running, completed, failed
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    reports = relationship("DiagnosticReport", back_populates="session", lazy="dynamic")


class DiagnosticReport(Base):
    __tablename__ = "diagnostic_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("diagnostic_sessions.id"), nullable=False)
    transaction_ref = Column(String(255), nullable=False)
    module = Column(String(100), nullable=False)
    root_cause = Column(Text, nullable=False)
    root_cause_detail = Column(Text, nullable=True)
    severity = Column(String(50), nullable=False)
    confidence_score = Column(Float, nullable=False, default=0.0)
    impacted_modules = Column(JSON, default=list)
    recommended_diagnostics = Column(JSON, default=list)
    suggested_next_steps = Column(JSON, default=list)
    supporting_evidence = Column(JSON, default=list)
    raw_page_data = Column(JSON, nullable=True)
    model_used = Column(String(100), nullable=True)
    tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    session = relationship("DiagnosticSession", back_populates="reports")
    screenshots = relationship("Screenshot", back_populates="report", lazy="dynamic")


class Screenshot(Base):
    __tablename__ = "screenshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("diagnostic_reports.id"), nullable=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("diagnostic_sessions.id"), nullable=True)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    page_url = Column(String(1000), nullable=True)
    page_type = Column(String(100), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    captured_at = Column(DateTime(timezone=True), server_default=func.now())
    extra_metadata = Column("metadata", JSON, default=dict)
    report = relationship("DiagnosticReport", back_populates="screenshots")


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(500), nullable=True)
    module = Column(String(100), nullable=True)
    document_type = Column(String(100), nullable=False)  # oracle_doc, rca, sql_pattern, config_guide
    chroma_doc_id = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    extra_metadata = Column("metadata", JSON, default=dict)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    action = Column(String(255), nullable=False)
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(String(255), nullable=True)
    correlation_id = Column(String(255), nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    details = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
