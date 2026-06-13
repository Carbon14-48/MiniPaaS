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

export default function Monitoring() {
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  console.log('[Monitoring] Component mounted');

  const loadData = async () => {
    console.log('[Monitoring] Loading data...');
    try {
      const token = localStorage.getItem('minipaas_access_token');
      const response = await fetch('/monitoring/metrics/summary', {
        credentials: 'include',
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      console.log('[Monitoring] Response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      console.log('[Monitoring] Got data:', data.length, 'items');
      setMetrics(data);
      setLastUpdate(new Date().toLocaleTimeString());
      setError(null);
    } catch (err: any) {
      console.error('[Monitoring] Error:', err);
      setError(err.message || 'Failed to load');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    console.log('[Monitoring] useEffect triggered');
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
    <div style={{ minHeight: '100vh', background: '#000', color: '#fff' }}>
      {/* Header */}
      <header style={{ background: '#111', borderBottom: '1px solid #333', padding: '20px 32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
          <Link to="/dashboard" style={{ color: '#fff', textDecoration: 'none', fontWeight: '700', fontSize: '20px', letterSpacing: '-0.5px' }}>
            ◀ MiniPaaS
          </Link>
          <nav style={{ display: 'flex', gap: '24px' }}>
            <Link to="/dashboard" style={{ color: '#666', textDecoration: 'none', fontSize: '14px', transition: 'color 0.2s' }}>Dashboard</Link>
            <Link to="/deployments" style={{ color: '#666', textDecoration: 'none', fontSize: '14px', transition: 'color 0.2s' }}>Deployments</Link>
            <span style={{ color: '#fff', fontSize: '14px', fontWeight: '500' }}>Monitoring</span>
          </nav>
        </div>
        <button 
          onClick={() => { setLoading(true); loadData(); }}
          style={{ 
            background: '#222', 
            border: '1px solid #444', 
            color: '#fff', 
            padding: '10px 20px', 
            borderRadius: '8px', 
            cursor: 'pointer', 
            fontSize: '14px',
            transition: 'all 0.2s'
          }}
        >
          ↻ Refresh
        </button>
      </header>

      <main style={{ padding: '32px', maxWidth: '1400px', margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '32px' }}>
          <h1 style={{ fontSize: '32px', fontWeight: '200', letterSpacing: '-1px' }}>Monitoring</h1>
          <span style={{ fontSize: '13px', color: '#555' }}>Updated: {lastUpdate || 'never'}</span>
        </div>

        {/* Stats Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '40px' }}>
          <div style={{ background: '#0a0a0a', border: '1px solid #222', borderRadius: '16px', padding: '24px' }}>
            <div style={{ fontSize: '36px', fontWeight: '200', color: '#fff', marginBottom: '4px' }}>{runningCount}</div>
            <div style={{ fontSize: '11px', color: '#555', textTransform: 'uppercase', letterSpacing: '1px' }}>Running</div>
          </div>
          <div style={{ background: '#0a0a0a', border: '1px solid #222', borderRadius: '16px', padding: '24px' }}>
            <div style={{ fontSize: '36px', fontWeight: '200', color: parseFloat(avgCpu) > 50 ? '#f59e0b' : '#fff', marginBottom: '4px' }}>{avgCpu}%</div>
            <div style={{ fontSize: '11px', color: '#555', textTransform: 'uppercase', letterSpacing: '1px' }}>Avg CPU</div>
          </div>
          <div style={{ background: '#0a0a0a', border: '1px solid #222', borderRadius: '16px', padding: '24px' }}>
            <div style={{ fontSize: '36px', fontWeight: '200', color: parseFloat(avgRam) > 50 ? '#f59e0b' : '#fff', marginBottom: '4px' }}>{avgRam}%</div>
            <div style={{ fontSize: '11px', color: '#555', textTransform: 'uppercase', letterSpacing: '1px' }}>Avg RAM</div>
          </div>
          <div style={{ background: '#0a0a0a', border: '1px solid #222', borderRadius: '16px', padding: '24px' }}>
            <div style={{ fontSize: '36px', fontWeight: '200', color: '#666', marginBottom: '4px' }}>{metrics.length}</div>
            <div style={{ fontSize: '11px', color: '#555', textTransform: 'uppercase', letterSpacing: '1px' }}>Total</div>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div style={{ background: '#1a0000', border: '1px solid #ff3333', color: '#ff4444', padding: '20px', borderRadius: '12px', marginBottom: '24px', fontSize: '14px' }}>
            ⚠️ Error: {error}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div style={{ color: '#444', padding: '60px', textAlign: 'center', fontSize: '14px' }}>
            Loading metrics...
          </div>
        )}

        {/* Table */}
        {!loading && (
          <div style={{ background: '#080808', border: '1px solid #1a1a1a', borderRadius: '16px', overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: '#111', borderBottom: '1px solid #222' }}>
                  <th style={{ padding: '20px', textAlign: 'left', fontWeight: '500', color: '#444', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '1px' }}>Application</th>
                  <th style={{ padding: '20px', textAlign: 'left', fontWeight: '500', color: '#444', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '1px' }}>Status</th>
                  <th style={{ padding: '20px', textAlign: 'right', fontWeight: '500', color: '#444', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '1px' }}>CPU</th>
                  <th style={{ padding: '20px', textAlign: 'right', fontWeight: '500', color: '#444', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '1px' }}>Memory</th>
                  <th style={{ padding: '20px', textAlign: 'right', fontWeight: '500', color: '#444', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '1px' }}>Last Update</th>
                </tr>
              </thead>
              <tbody>
                {metrics.map((m, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #111' }}>
                    <td style={{ padding: '20px', fontSize: '15px', fontWeight: '500' }}>{m.app_id}</td>
                    <td style={{ padding: '20px' }}>
                      <span style={{ 
                        background: m.status === 'running' ? '#0a1a0a' : '#1a0a0a',
                        color: m.status === 'running' ? '#00ff66' : '#ff4444',
                        padding: '6px 12px', 
                        borderRadius: '6px', 
                        fontSize: '12px',
                        fontWeight: '500'
                      }}>
                        {m.status}
                      </span>
                    </td>
                    <td style={{ padding: '20px', textAlign: 'right', fontSize: '14px', fontFamily: 'monospace', color: '#888' }}>
                      {m.cpu_percent?.toFixed(2)}%
                    </td>
                    <td style={{ padding: '20px', textAlign: 'right', fontSize: '14px', fontFamily: 'monospace', color: '#888' }}>
                      {m.memory_percent?.toFixed(2)}%
                    </td>
                    <td style={{ padding: '20px', textAlign: 'right', fontSize: '12px', color: '#444' }}>
                      {m.collected_at ? new Date(m.collected_at).toLocaleTimeString() : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            {metrics.length === 0 && (
              <div style={{ padding: '60px', textAlign: 'center', color: '#333', fontSize: '14px' }}>
                No deployments found
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}