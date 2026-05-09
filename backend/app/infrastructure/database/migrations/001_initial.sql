-- Oracle Fusion AI Diagnostic Agent — Initial Schema
-- Run once on fresh database

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'analyst',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS diagnostic_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    browser_session_id VARCHAR(255),
    tenant_url VARCHAR(500) NOT NULL,
    module VARCHAR(100) NOT NULL,
    transaction_ref VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'running',
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS diagnostic_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES diagnostic_sessions(id) ON DELETE CASCADE,
    transaction_ref VARCHAR(255) NOT NULL,
    module VARCHAR(100) NOT NULL,
    root_cause TEXT NOT NULL,
    root_cause_detail TEXT,
    severity VARCHAR(50) NOT NULL,
    confidence_score FLOAT NOT NULL DEFAULT 0.0,
    impacted_modules JSONB DEFAULT '[]',
    recommended_diagnostics JSONB DEFAULT '[]',
    suggested_next_steps JSONB DEFAULT '[]',
    supporting_evidence JSONB DEFAULT '[]',
    raw_page_data JSONB,
    model_used VARCHAR(100),
    tokens_used INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS screenshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID REFERENCES diagnostic_reports(id) ON DELETE SET NULL,
    session_id UUID REFERENCES diagnostic_sessions(id) ON DELETE SET NULL,
    filename VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    page_url VARCHAR(1000),
    page_type VARCHAR(100),
    file_size_bytes INTEGER,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS knowledge_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    source VARCHAR(500),
    module VARCHAR(100),
    document_type VARCHAR(100) NOT NULL,
    chroma_doc_id VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    action VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    correlation_id VARCHAR(255),
    ip_address VARCHAR(50),
    user_agent VARCHAR(500),
    details JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_diagnostic_sessions_user ON diagnostic_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_diagnostic_sessions_module ON diagnostic_sessions(module);
CREATE INDEX IF NOT EXISTS idx_diagnostic_sessions_status ON diagnostic_sessions(status);
CREATE INDEX IF NOT EXISTS idx_diagnostic_reports_session ON diagnostic_reports(session_id);
CREATE INDEX IF NOT EXISTS idx_diagnostic_reports_module ON diagnostic_reports(module);
CREATE INDEX IF NOT EXISTS idx_diagnostic_reports_severity ON diagnostic_reports(severity);
CREATE INDEX IF NOT EXISTS idx_screenshots_report ON screenshots(report_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
