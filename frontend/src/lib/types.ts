export interface DiagnosticReport {
  session_id: string;
  report_id?: string;
  module: string;
  transaction_ref: string;
  root_cause: string;
  root_cause_detail?: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  confidence_score: number;
  impacted_modules: string[];
  recommended_diagnostics: string[];
  suggested_next_steps: string[];
  supporting_evidence: string[];
  screenshot_path?: string;
  knowledge_context_count: number;
  page_url?: string;
  analyzed_at: string;
}

export interface BrowserSession {
  session_id: string;
  status: string;
  tenant_url: string;
  authenticated: boolean;
  current_url?: string;
  created_at: string;
  last_used_at: string;
}

export interface KnowledgeResult {
  content: string;
  metadata?: Record<string, any>;
  similarity_score?: number;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}
