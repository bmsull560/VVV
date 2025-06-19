import React, { useState } from 'react';

export default function AnalysisForm({ onAnalysisComplete }) {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Step 1: Start the analysis and get an entity ID
      const startRes = await fetch('http://localhost:5001/api/start-analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content })
      });

      const startData = await startRes.json();
      if (!startRes.ok) {
        throw new Error(startData.error || 'Failed to start analysis');
      }

      const { id: entityId } = startData;

      // Step 2: Use the entity ID to discover value drivers and personas
      const discoverRes = await fetch(`http://localhost:5001/api/discover-value/${entityId}`, {
        method: 'POST',
      });

      const discoverData = await discoverRes.json();
      if (!discoverRes.ok) {
        throw new Error(discoverData.error || 'Failed to discover value');
      }

      // Pass the final, combined results to the parent component
      onAnalysisComplete(discoverData);

    } catch (err) {
      setError(err.message || 'An unexpected network error occurred.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded shadow p-6 w-full max-w-md mb-8">
      <h2 className="text-xl font-semibold mb-4">Start New Analysis</h2>
      <div className="mb-4">
        <label className="block mb-1 font-medium">Content</label>
        <textarea value={content} onChange={e => setContent(e.target.value)} required className="w-full border rounded p-2" rows={3} />
      </div>
      <div className="mb-4">
        <label className="block mb-1 font-medium">Content Type</label>
        <select value={contentType} onChange={e => setContentType(e.target.value)} className="w-full border rounded p-2">
          <option value="text">Text</option>
          <option value="spreadsheet">Spreadsheet</option>
          <option value="pdf">PDF</option>
        </select>
      </div>
      <div className="mb-4">
        <label className="block mb-1 font-medium">Your User ID</label>
        <input value={creatorId} onChange={e => setCreatorId(e.target.value)} className="w-full border rounded p-2" />
      </div>
      {error && <div className="text-red-500 mb-2">{error}</div>}
      <button type="submit" disabled={loading} className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded">
        {loading ? 'Starting...' : 'Start Analysis'}
      </button>
    </form>
  );
}
