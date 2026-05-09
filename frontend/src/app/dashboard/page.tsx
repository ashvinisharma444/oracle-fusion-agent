'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

const MODULES = [
  { name: 'Subscription Mgmt', color: 'from-blue-600 to-blue-700', desc: 'Diagnose subscription lifecycle issues' },
  { name: 'Order Management', color: 'from-purple-600 to-purple-700', desc: 'Analyze order fulfillment failures' },
  { name: 'Orchestration (DOO)', color: 'from-amber-600 to-amber-700', desc: 'Debug orchestration process steps' },
  { name: 'Billing & Revenue', color: 'from-green-600 to-green-700', desc: 'Investigate billing anomalies' },
  { name: 'Pricing Engine', color: 'from-rose-600 to-rose-700', desc: 'Analyze pricing configuration issues' },
  { name: 'Installed Base', color: 'from-cyan-600 to-cyan-700', desc: 'Review installed base records' },
];

export default function DashboardPage() {
  const [health, setHealth] = useState<{ status: string; components: Record<string, boolean> } | null>(null);

  useEffect(() => {
    api.health().then(setHealth).catch(() => {});
  }, []);

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Oracle Fusion AI Diagnostic Agent</h1>
        <p className="text-gray-400 mt-1">AI-powered root cause analysis for Oracle Fusion Cloud — Phase 1 (Read-Only)</p>
      </div>

      {health && (
        <div className={`mb-6 p-4 rounded-xl border ${health.status === 'healthy' ? 'bg-green-500/10 border-green-500/30' : 'bg-yellow-500/10 border-yellow-500/30'}`}>
          <div className="flex items-center gap-3">
            <div className={`w-2.5 h-2.5 rounded-full ${health.status === 'healthy' ? 'bg-green-400' : 'bg-yellow-400'}`} />
            <span className="text-sm font-medium text-white">System {health.status}</span>
            {Object.entries(health.components).map(([key, ok]) => (
              <span key={key} className={`text-xs px-2 py-0.5 rounded ${ok ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                {key}: {ok ? '✓' : '✗'}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-3 gap-4 mb-8">
        {MODULES.map(m => (
          <div key={m.name} className="bg-gray-900 border border-gray-800 rounded-2xl p-5 hover:border-gray-700 transition-colors cursor-pointer">
            <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${m.color} mb-3 flex items-center justify-center text-white text-lg font-bold`}>
              {m.name[0]}
            </div>
            <h3 className="text-white font-semibold text-sm">{m.name}</h3>
            <p className="text-gray-500 text-xs mt-1">{m.desc}</p>
          </div>
        ))}
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
        <h2 className="text-white font-semibold mb-4">Quick Start</h2>
        <div className="space-y-3 text-sm text-gray-400">
          <div className="flex items-start gap-3">
            <span className="text-red-500 font-bold">1.</span>
            <span>Go to <strong className="text-white">Run Diagnostic</strong> and enter a subscription, order, or orchestration number.</span>
          </div>
          <div className="flex items-start gap-3">
            <span className="text-red-500 font-bold">2.</span>
            <span>The agent will authenticate into Oracle Fusion, navigate to the record, and capture page data.</span>
          </div>
          <div className="flex items-start gap-3">
            <span className="text-red-500 font-bold">3.</span>
            <span>Gemini 2.5 Pro analyzes the data against the knowledge base and generates an RCA with remediation steps.</span>
          </div>
          <div className="flex items-start gap-3">
            <span className="text-red-500 font-bold">4.</span>
            <span>Results are saved in <strong className="text-white">Report History</strong> for audit and future reference.</span>
          </div>
        </div>
      </div>
    </div>
  );
}
