import { useState, useEffect } from 'react';
import { apiClient } from './api/client';
import type { HealthStatus } from './api/client';

function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const data = await apiClient.getHealth();
        setHealth(data);
        setError(null);
      } catch (err) {
        console.error("Health check failed:", err);
        setError("Backend unavailable");
      } finally {
        setLoading(false);
      }
    };

    checkHealth();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-6 border-b pb-4">
          ReguLens
        </h1>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-gray-600 font-medium">Backend:</span>
            {loading ? (
              <span className="text-blue-500 font-semibold animate-pulse">Checking backend...</span>
            ) : error ? (
              <span className="text-red-500 font-semibold">{error}</span>
            ) : (
              <span className="text-green-500 font-semibold">Connected</span>
            )}
          </div>

          {!loading && !error && health && (
            <div className="flex items-center justify-between">
              <span className="text-gray-600 font-medium">Status:</span>
              <span className="bg-gray-100 text-gray-800 px-3 py-1 rounded-full text-sm font-mono">
                {health.status}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
