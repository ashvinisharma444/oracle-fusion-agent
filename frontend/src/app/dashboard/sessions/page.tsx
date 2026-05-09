'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { BrowserSession } from '@/lib/types';

const STATUS_STYLES: Record<string, string> = {
  active: 'bg-green-500/20 text-green-400 border border-green-500/30',
  idle: 'bg-blue-500/20 text-blue-400 border border-blue-500/30',
  initializing: 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30',
  error: 'bg-red-500/20 text-red-400 border border-red-500/30',
  mfa_pending: 'bg-purple-500/20 text-purple-400 border border-purple-500/30',
  closed: 'bg-gray-500/20 text-gray-400 border border-gray-500/30',
};

export default function SessionsPage() {
  const [sessions, setSessions] = useState<BrowserSession[]>([]);
  const [tenantUrl, setTenantUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);

  const load = async () => {
    setLoading(true);
    try { setSessions(await api.getSessions()); } catch {} finally { setLoading(false); }
  };

  useEffect(() => { load(); const t = setInterval(load, 15000); return () => clearInterval(t); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try { await api.createSession(tenantUrl); setTenantUrl(''); await load(); } catch {} finally { setCreating(false); }
  };

  const handleClose = async (id: string) => {
    try { await api.closeSession(id); await load(); } catch {}
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Browser Sessions</h1>
        <p className="text-gray-400 mt-1">Manage active Oracle Fusion browser automation sessions</p>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 mb-6">
        <form onSubmit={handleCreate} className="flex gap-3">
          <input value={tenantUrl} onChange={e => setTenantUrl(e.target.value)} required
            placeholder="https://tenant.fa.us2.oraclecloud.com"
            className="flex-1 px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-red-500 text-sm" />
          <button type="submit" disabled={creating}
            className="px-5 py-2.5 bg-red-600 hover:bg-red-500 text-white font-medium rounded-xl text-sm transition-colors">
            {creating ? 'Connecting...' : '+ New Session'}
          </button>
        </form>
      </div>

      {loading && sessions.length === 0 ? (
        <div className="text-center text-gray-500 py-12">Loading sessions...</div>
      ) : sessions.length === 0 ? (
        <div className="text-center text-gray-500 py-12">No active sessions. Create one to start diagnosing.</div>
      ) : (
        <div className="space-y-3">
          {sessions.map(s => (
            <div key={s.session_id} className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <span className={`px-2.5 py-1 rounded-lg text-xs font-semibold ${STATUS_STYLES[s.status] || STATUS_STYLES.closed}`}>
                    {s.status}
                  </span>
                  <span className={`text-xs px-2 py-1 rounded ${s.authenticated ? 'bg-green-500/20 text-green-400' : 'bg-gray-700 text-gray-400'}`}>
                    {s.authenticated ? '🔓 Authenticated' : '🔒 Not authenticated'}
                  </span>
                </div>
                <button onClick={() => handleClose(s.session_id)}
                  className="text-xs text-red-400 hover:text-red-300 px-3 py-1.5 border border-red-500/30 rounded-lg">
                  Close Session
                </button>
              </div>
              <p className="text-white text-sm font-medium">{s.tenant_url}</p>
              {s.current_url && <p className="text-gray-500 text-xs mt-1 truncate">{s.current_url}</p>}
              <div className="flex gap-4 mt-2 text-xs text-gray-600">
                <span>Created: {new Date(s.created_at).toLocaleTimeString()}</span>
                <span>Last used: {new Date(s.last_used_at).toLocaleTimeString()}</span>
                <span className="font-mono text-gray-700">ID: {s.session_id.slice(0, 8)}...</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
