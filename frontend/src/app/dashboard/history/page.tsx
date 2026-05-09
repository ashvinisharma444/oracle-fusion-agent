'use client';
export default function HistoryPage() {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Report History</h1>
        <p className="text-gray-400 mt-1">Audit trail of all diagnostic analyses</p>
      </div>
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-12 text-center">
        <p className="text-gray-500">Connect to the API to view report history. Reports are stored in PostgreSQL and accessible via <code className="text-gray-400 bg-gray-800 px-1.5 py-0.5 rounded">GET /api/v1/reports</code></p>
      </div>
    </div>
  );
}
