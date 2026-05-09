'use client';
import { useState } from 'react';
import { api } from '@/lib/api';

const MODULES = ['', 'subscription', 'order', 'orchestration', 'billing', 'pricing'];

export default function KnowledgePage() {
  const [query, setQuery] = useState('');
  const [module, setModule] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res: any = await api.searchKnowledge(query, module || undefined);
      setResults(res.results || []);
    } catch {} finally { setLoading(false); }
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Knowledge Search</h1>
        <p className="text-gray-400 mt-1">Semantic search across Oracle docs, RCA history, SQL patterns, and config guides</p>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 mb-6">
        <form onSubmit={handleSearch} className="space-y-4">
          <input value={query} onChange={e => setQuery(e.target.value)} required
            placeholder="e.g. subscription status pending activation issue"
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-red-500" />
          <div className="flex gap-3">
            <select value={module} onChange={e => setModule(e.target.value)}
              className="flex-1 px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-xl text-gray-300 focus:outline-none focus:border-red-500 text-sm">
              {MODULES.map(m => <option key={m} value={m}>{m || 'All Modules'}</option>)}
            </select>
            <button type="submit" disabled={loading}
              className="px-6 py-2.5 bg-red-600 hover:bg-red-500 text-white font-medium rounded-xl text-sm transition-colors">
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>
        </form>
      </div>

      {results.length > 0 && (
        <div className="space-y-3">
          {results.map((r, i) => (
            <div key={i} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <p className="text-gray-300 text-sm leading-relaxed">{r.content}</p>
              {r.similarity_score && <p className="text-gray-600 text-xs mt-2">Relevance: {(r.similarity_score * 100).toFixed(0)}%</p>}
            </div>
          ))}
        </div>
      )}
      {results.length === 0 && query && !loading && (
        <p className="text-center text-gray-500 py-8">No results found. Try a different query or ingest more documents.</p>
      )}
    </div>
  );
}
