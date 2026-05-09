'use client';
import { useState } from 'react';
import { api } from '@/lib/api';
import type { DiagnosticReport } from '@/lib/types';

const SEVERITY_STYLES: Record<string, string> = {
  critical: 'severity-critical',
  high: 'severity-high',
  medium: 'severity-medium',
  low: 'severity-low',
  info: 'severity-info',
};

const MODULES = [
  { value: 'subscription', label: 'Subscription', field: 'subscription_number', placeholder: 'e.g. SUB-000123' },
  { value: 'order', label: 'Order', field: 'order_number', placeholder: 'e.g. OM-000456' },
  { value: 'orchestration', label: 'Orchestration (DOO)', field: 'orchestration_id', placeholder: 'e.g. DOO-000789' },
];

export default function DiagnosticsPage() {
  const [module, setModule] = useState('subscription');
  const [transactionRef, setTransactionRef] = useState('');
  const [tenantUrl, setTenantUrl] = useState('');
  const [issueDesc, setIssueDesc] = useState('');
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<DiagnosticReport | null>(null);
  const [error, setError] = useState('');

  const selectedModule = MODULES.find(m => m.value === module)!;

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setReport(null);
    try {
      let result: any;
      if (module === 'subscription') {
        result = await api.analyzeSubscription({ subscription_number: transactionRef, tenant_url: tenantUrl, issue_description: issueDesc || undefined });
      } else if (module === 'order') {
        result = await api.analyzeOrder({ order_number: transactionRef, tenant_url: tenantUrl, issue_description: issueDesc || undefined });
      } else {
        result = await api.analyzeOrchestration({ orchestration_id: transactionRef, tenant_url: tenantUrl, issue_description: issueDesc || undefined });
      }
      setReport(result as DiagnosticReport);
    } catch (err: any) {
      setError(err.message || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Run Diagnostic</h1>
        <p className="text-gray-400 mt-1">AI-powered RCA using Gemini 2.5 Pro · Read-Only</p>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 mb-6">
        <form onSubmit={handleAnalyze} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Module</label>
            <div className="flex gap-2">
              {MODULES.map(m => (
                <button key={m.value} type="button" onClick={() => setModule(m.value)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors
                    ${module === m.value ? 'bg-red-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white'}`}>
                  {m.label}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">{selectedModule.label} Number</label>
              <input value={transactionRef} onChange={e => setTransactionRef(e.target.value)} required
                placeholder={selectedModule.placeholder}
                className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-red-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">Oracle Fusion Tenant URL</label>
              <input value={tenantUrl} onChange={e => setTenantUrl(e.target.value)} required
                placeholder="https://tenant.fa.us2.oraclecloud.com"
                className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-red-500" />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">Issue Description (optional)</label>
            <textarea value={issueDesc} onChange={e => setIssueDesc(e.target.value)} rows={3}
              placeholder="Describe the observed issue or anomaly..."
              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-red-500 resize-none" />
          </div>

          {error && <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">{error}</div>}

          <button type="submit" disabled={loading}
            className="w-full py-3 bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white font-semibold rounded-xl transition-colors">
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin w-5 h-5" viewBox="0 0 24 24" fill="none"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
                Analyzing — navigating Fusion, capturing data, running Gemini RCA...
              </span>
            ) : 'Run AI Diagnostic'}
          </button>
        </form>
      </div>

      {report && (
        <div className="space-y-4">
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-lg font-bold text-white">RCA Report</h2>
                <p className="text-gray-500 text-sm">{report.transaction_ref} · {report.module} · {new Date(report.analyzed_at).toLocaleString()}</p>
              </div>
              <div className={`px-3 py-1.5 rounded-lg text-sm font-semibold uppercase tracking-wide ${SEVERITY_STYLES[report.severity] || 'severity-info'}`}>
                {report.severity}
              </div>
            </div>

            <div className="mb-4">
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-2">Root Cause</h3>
              <p className="text-white font-medium">{report.root_cause}</p>
              {report.root_cause_detail && <p className="text-gray-400 text-sm mt-2">{report.root_cause_detail}</p>}
            </div>

            <div className="mb-4">
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-2">Confidence</h3>
              <div className="flex items-center gap-3">
                <div className="flex-1 bg-gray-800 rounded-full h-2">
                  <div className="bg-red-500 h-2 rounded-full" style={{ width: `${Math.round(report.confidence_score * 100)}%` }} />
                </div>
                <span className="text-white font-medium text-sm">{Math.round(report.confidence_score * 100)}%</span>
              </div>
            </div>

            {report.impacted_modules.length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-2">Impacted Modules</h3>
                <div className="flex flex-wrap gap-2">
                  {report.impacted_modules.map((m, i) => (
                    <span key={i} className="px-2.5 py-1 bg-gray-800 border border-gray-700 rounded-lg text-gray-300 text-xs">{m}</span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {report.recommended_diagnostics.length > 0 && (
            <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Recommended Diagnostics</h3>
              <ul className="space-y-2">
                {report.recommended_diagnostics.map((d, i) => (
                  <li key={i} className="flex items-start gap-3 text-sm text-gray-300">
                    <span className="text-red-500 font-bold mt-0.5">{i + 1}.</span>{d}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {report.suggested_next_steps.length > 0 && (
            <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Suggested Next Steps</h3>
              <ul className="space-y-2">
                {report.suggested_next_steps.map((s, i) => (
                  <li key={i} className="flex items-start gap-3 text-sm text-gray-300">
                    <span className="text-amber-500 font-bold mt-0.5">→</span>{s}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
