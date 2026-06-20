import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

interface Metric {
  app_id: string;
  user_id: number;
  cpu_percent: number;
  memory_percent: number;
  status: string;
  collected_at: string;
}

function getErrorMessage(err: unknown): string {
  return err instanceof Error ? err.message : 'Failed to load';
}

export default function Monitoring() {
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  const loadData = async () => {
    try {
      const token = localStorage.getItem('minipaas_access_token');
      const response = await fetch('/monitoring/metrics/summary', {
        credentials: 'include',
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      setMetrics(data);
      setLastUpdate(new Date().toLocaleTimeString());
      setError(null);
    } catch (err: unknown) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 15000);
    return () => clearInterval(interval);
  }, []);

  const runningCount = metrics.filter(m => m.status === 'running').length;
  const totalCpu = metrics.reduce((acc, m) => acc + (m.cpu_percent || 0), 0);
  const totalRam = metrics.reduce((acc, m) => acc + (m.memory_percent || 0), 0);
  const avgCpu = metrics.length > 0 ? (totalCpu / metrics.length).toFixed(1) : '0';
  const avgRam = metrics.length > 0 ? (totalRam / metrics.length).toFixed(1) : '0';

  return (
    <div className="min-h-screen bg-bg-primary text-text-primary">
      {/* Header */}
      <header className="bg-bg-card border-b border-border px-8 py-5 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <Link to="/dashboard" className="text-text-primary no-underline font-bold text-xl tracking-tight">
            MiniPaaS
          </Link>
          <nav className="flex gap-6">
            <Link to="/dashboard" className="text-text-muted hover:text-text-primary text-sm no-underline">Dashboard</Link>
            <Link to="/deployments" className="text-text-muted hover:text-text-primary text-sm no-underline">Deployments</Link>
            <span className="text-text-primary text-sm font-medium">Monitoring</span>
          </nav>
        </div>
        <button 
          onClick={() => { setLoading(true); loadData(); }}
          className="bg-bg-hover border border-border text-text-primary px-5 py-2.5 rounded-lg cursor-pointer text-sm hover:bg-border"
        >
          Refresh
        </button>
      </header>

      <main className="px-8 py-8 max-w-7xl mx-auto">
        <div className="flex items-baseline justify-between mb-8">
          <h1 className="text-3xl font-light tracking-tight">Monitoring</h1>
          <span className="text-xs text-text-muted">Updated: {lastUpdate || 'never'}</span>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-4 gap-4 mb-10">
          <div className="bg-bg-card border border-border rounded-2xl p-6">
            <div className="text-4xl font-light text-text-primary mb-1">{runningCount}</div>
            <div className="text-xs text-text-muted uppercase tracking-widest">Running</div>
          </div>
          <div className="bg-bg-card border border-border rounded-2xl p-6">
            <div className="text-4xl font-light text-text-primary mb-1">{avgCpu}%</div>
            <div className="text-xs text-text-muted uppercase tracking-widest">Avg CPU</div>
          </div>
          <div className="bg-bg-card border border-border rounded-2xl p-6">
            <div className="text-4xl font-light text-text-primary mb-1">{avgRam}%</div>
            <div className="text-xs text-text-muted uppercase tracking-widest">Avg RAM</div>
          </div>
          <div className="bg-bg-card border border-border rounded-2xl p-6">
            <div className="text-4xl font-light text-text-primary mb-1">{metrics.length}</div>
            <div className="text-xs text-text-muted uppercase tracking-widest">Total</div>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-accent-red/10 border border-accent-red/30 text-accent-red p-5 rounded-xl mb-6 text-sm">
            Error: {error}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="text-text-muted text-center py-16 text-sm">
            Loading metrics...
          </div>
        )}

        {/* Table */}
        {!loading && (
          <div className="bg-black border border-border rounded-2xl overflow-hidden">
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-bg-card border-b border-border">
                  <th className="px-5 py-5 text-left font-medium text-text-muted text-xs uppercase tracking-wider">Application</th>
                  <th className="px-5 py-5 text-left font-medium text-text-muted text-xs uppercase tracking-wider">Status</th>
                  <th className="px-5 py-5 text-right font-medium text-text-muted text-xs uppercase tracking-wider">CPU</th>
                  <th className="px-5 py-5 text-right font-medium text-text-muted text-xs uppercase tracking-wider">Memory</th>
                  <th className="px-5 py-5 text-right font-medium text-text-muted text-xs uppercase tracking-wider">Last Update</th>
                </tr>
              </thead>
              <tbody>
                {metrics.map((m, i) => (
                  <tr key={i} className="border-b border-border/50">
                    <td className="px-5 py-5 text-sm font-medium text-text-primary">{m.app_id}</td>
                    <td className="px-5 py-5">
                      <span className={`px-3 py-1.5 rounded-md text-xs font-medium ${
                        m.status === 'running'
                          ? 'bg-accent-white/10 text-text-primary'
                          : 'bg-accent-red/10 text-accent-red'
                      }`}>
                        {m.status}
                      </span>
                    </td>
                    <td className="px-5 py-5 text-right text-sm font-mono text-text-secondary">
                      {m.cpu_percent?.toFixed(2)}%
                    </td>
                    <td className="px-5 py-5 text-right text-sm font-mono text-text-secondary">
                      {m.memory_percent?.toFixed(2)}%
                    </td>
                    <td className="px-5 py-5 text-right text-xs text-text-muted">
                      {m.collected_at ? new Date(m.collected_at).toLocaleTimeString() : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            {metrics.length === 0 && (
              <div className="text-text-muted text-center py-16 text-sm">
                No deployments found
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
