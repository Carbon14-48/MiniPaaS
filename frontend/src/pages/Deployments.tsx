import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { deployerApiService, Deployment } from '../lib/api';
import DeploymentCard from '../components/ui/DeploymentCard';
import LogViewer from '../components/ui/LogViewer';
import { Link, useNavigate } from 'react-router-dom';

function getStatusCode(err: unknown): number | null {
  if (typeof err !== 'object' || err === null) return null;
  const candidate = err as { response?: { status?: number }; status?: number };
  return candidate.response?.status ?? candidate.status ?? null;
}

export default function Deployments() {
  const { accessToken, logout } = useAuth();
  const navigate = useNavigate();
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedLogs, setSelectedLogs] = useState<{ logs: string; source: string } | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const loadDeployments = useCallback(async () => {
    if (!accessToken) return;
    try {
      const data = await deployerApiService.getDeployments(accessToken);
      setDeployments(data.deployments);
      setError(null);
      setLastRefresh(new Date());
    } catch (err: unknown) {
      if (getStatusCode(err) === 401) {
        setError('Session expired. Please login again.');
        setTimeout(() => {
          logout();
          navigate('/login');
        }, 2000);
      } else {
        console.error(err);
      }
    }
  }, [accessToken, logout, navigate]);

  useEffect(() => {
    if (!accessToken) return;
    setLoading(true);
    loadDeployments().finally(() => setLoading(false));
    
    // Auto-refresh every 5 seconds
    const interval = setInterval(() => {
      loadDeployments();
    }, 5000);
    
    return () => clearInterval(interval);
  }, [accessToken, loadDeployments]);

  const handleStop = async (id: string) => {
    if (!accessToken) return;
    try {
      await deployerApiService.stopDeployment(accessToken, id);
      await loadDeployments();
    } catch (err) {
      setError('Failed to stop deployment');
      console.error(err);
    }
  };

  const handleStart = async (id: string) => {
    if (!accessToken) return;
    try {
      await deployerApiService.startDeployment(accessToken, id);
      await loadDeployments();
    } catch (err) {
      setError('Failed to start deployment');
      console.error(err);
    }
  };

  const handleRestart = async (id: string) => {
    if (!accessToken) return;
    try {
      await deployerApiService.restartDeployment(accessToken, id);
      await loadDeployments();
    } catch (err) {
      setError('Failed to restart deployment');
      console.error(err);
    }
  };

  const handleDelete = async (id: string) => {
    if (!accessToken) return;
    if (!confirm('Are you sure you want to delete this deployment?')) return;
    try {
      await deployerApiService.deleteDeployment(accessToken, id);
      await loadDeployments();
    } catch (err) {
      setError('Failed to delete deployment');
      console.error(err);
    }
  };

  const handleViewLogs = async (id: string) => {
    if (!accessToken) return;
    try {
      const logsData = await deployerApiService.getDeploymentLogs(accessToken, id);
      setSelectedLogs(logsData);
    } catch (err) {
      setError('Failed to load logs');
      console.error(err);
    }
  };

  const runningCount = deployments.filter((d) => d.status === 'running').length;
  const stoppedCount = deployments.filter((d) => d.status === 'stopped').length;
  const failedCount = deployments.filter((d) => d.status === 'failed' || d.status === 'blocked').length;
  const buildingCount = deployments.filter((d) => d.status === 'building' || d.status === 'deploying').length;

  return (
    <div className="min-h-screen bg-bg-primary text-text-primary">
      <nav className="bg-bg-card border-b border-border px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link to="/dashboard" className="text-xl font-bold text-text-primary">MiniPaaS</Link>
            <div className="flex gap-4">
              <Link to="/dashboard" className="text-text-secondary hover:text-text-primary transition">Dashboard</Link>
              <Link to="/deployments" className="text-text-primary font-medium">Deployments</Link>
<Link to="/monitoring" className="text-text-secondary hover:text-text-primary transition">Monitoring</Link>
              <Link to="/repos" className="text-text-secondary hover:text-text-primary transition">Repositories</Link>
             </div>
           </div>
          <button
            onClick={() => loadDeployments()}
            className="px-3 py-1.5 bg-bg-hover hover:bg-border text-text-primary text-sm rounded transition flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold">Your Deployments</h1>
            <p className="text-text-secondary mt-1 text-sm">
              Auto-refreshes every 5 seconds - Last: {lastRefresh.toLocaleTimeString()}
            </p>
          </div>
          <Link
            to="/repos"
            className="px-4 py-2 bg-accent-white text-black hover:bg-accent-light rounded-lg transition"
          >
            New Deployment
          </Link>
        </div>

        <div className="grid grid-cols-4 gap-4 mb-8">
          <div className="bg-bg-card rounded-lg p-4 border border-border">
            <div className="text-2xl font-bold text-text-primary">{runningCount}</div>
            <div className="text-text-secondary">Running</div>
          </div>
          <div className="bg-bg-card rounded-lg p-4 border border-border">
            <div className="text-2xl font-bold text-text-primary">{buildingCount}</div>
            <div className="text-text-secondary">Building</div>
          </div>
          <div className="bg-bg-card rounded-lg p-4 border border-border">
            <div className="text-2xl font-bold text-text-primary">{failedCount}</div>
            <div className="text-text-secondary">Failed/Blocked</div>
          </div>
          <div className="bg-bg-card rounded-lg p-4 border border-border">
            <div className="text-2xl font-bold text-text-primary">{stoppedCount}</div>
            <div className="text-text-secondary">Stopped</div>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-accent-red/10 border border-accent-red/30 rounded-lg text-accent-red">
            {error}
            <button
              onClick={() => window.location.href = '/'}
              className="ml-4 underline hover:no-underline"
            >
              Go to Login
            </button>
          </div>
        )}

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-accent-white"></div>
          </div>
        ) : deployments.length === 0 ? (
          <div className="text-center py-12 bg-bg-card rounded-lg border border-border">
            <p className="text-text-secondary mb-4">No deployments yet</p>
            <Link
              to="/repos"
              className="px-4 py-2 bg-accent-white text-black hover:bg-accent-light rounded-lg transition inline-block"
            >
              Deploy your first app
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {deployments.map((deployment) => (
              <DeploymentCard
                key={deployment.id}
                deployment={deployment}
                onStop={handleStop}
                onStart={handleStart}
                onRestart={handleRestart}
                onDelete={handleDelete}
                onViewLogs={handleViewLogs}
              />
            ))}
          </div>
        )}
      </main>

      {selectedLogs && (
        <LogViewer
          logs={selectedLogs.logs}
          source={selectedLogs.source}
          onClose={() => setSelectedLogs(null)}
        />
      )}
    </div>
  );
}
