'use client';
export default function ScreenshotsPage() {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Screenshots</h1>
        <p className="text-gray-400 mt-1">Captured Fusion UI screenshots from diagnostic sessions</p>
      </div>
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-12 text-center">
        <p className="text-gray-500">Screenshots are saved to <code className="text-gray-400 bg-gray-800 px-1.5 py-0.5 rounded">/tmp/screenshots</code> on the backend and catalogued in the database. Run a diagnostic to capture your first screenshot.</p>
      </div>
    </div>
  );
}
