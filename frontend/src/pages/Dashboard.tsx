import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { deployerApiService, type Deployment } from '../lib/api';
import { Link } from 'react-router-dom';

export default function Dashboard() {
  const { user, logout, refreshAccessToken, accessToken, refreshToken } = useAuth();
  const [deployments, setDeployments] = useState<Deployment[]>([]);

  useEffect(() => {
    if (accessToken) {
      loadStats();
    }
  }, [accessToken]);

  const loadStats = async () => {
    if (!accessToken) return;
    try {
      const data = await deployerApiService.getDeployments(accessToken);
      setDeployments(data.deployments || []);
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  };

  const runningCount = deployments.filter(d => d.status === 'running').length;
  const buildingCount = deployments.filter(d => d.status === 'building' || d.status === 'deploying').length;
  const stoppedCount = deployments.filter(d => d.status === 'stopped').length;

  return (
    <div className="min-h-screen bg-bg-primary">
      <nav className="bg-bg-card border-b border-border px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link to="/dashboard" className="text-xl font-bold text-text-primary">MiniPaaS</Link>
            <div className="flex gap-4">
              <Link to="/repos" className="text-text-secondary hover:text-text-primary transition">Repositories</Link>
              <Link to="/deployments" className="text-text-secondary hover:text-text-primary transition">Deployments</Link>
              <Link to="/monitoring" className="text-text-secondary hover:text-text-primary transition">Monitoring</Link>
              <Link to="/deploy/new" className="px-4 py-1 bg-accent-white text-black hover:bg-accent-light rounded-lg transition text-sm font-medium">+ New Deploy</Link>
            </div>
          </div>
          <button
            onClick={logout}
            className="px-4 py-2 text-sm font-medium bg-transparent border border-accent-red/50 text-accent-red hover:bg-accent-red/10 rounded-md"
          >
            Logout
          </button>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 px-4">
        <h1 className="text-2xl font-bold text-text-primary mb-6">Dashboard</h1>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-bg-card rounded-lg p-4 border border-border">
            <div className="text-3xl font-bold text-text-primary">{deployments.length}</div>
            <div className="text-text-secondary text-sm">Total Deployments</div>
          </div>
          <div className="bg-bg-card rounded-lg p-4 border border-border">
            <div className="text-3xl font-bold text-text-primary">{runningCount}</div>
            <div className="text-text-secondary text-sm">Running</div>
          </div>
          <div className="bg-bg-card rounded-lg p-4 border border-border">
            <div className="text-3xl font-bold text-text-primary">{buildingCount}</div>
            <div className="text-text-secondary text-sm">Building</div>
          </div>
          <div className="bg-bg-card rounded-lg p-4 border border-border">
            <div className="text-3xl font-bold text-text-primary">{stoppedCount}</div>
            <div className="text-text-secondary text-sm">Stopped</div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-bg-card rounded-lg p-4 border border-border mb-6">
          <h2 className="text-lg font-semibold text-text-primary mb-4">Quick Actions</h2>
          <div className="flex gap-4">
            <Link
              to="/repos"
              className="px-4 py-2 bg-bg-hover hover:bg-border text-text-primary rounded-lg transition"
            >
              Browse Repositories
            </Link>
            <Link
              to="/monitoring"
              className="px-4 py-2 bg-bg-hover hover:bg-border text-text-primary rounded-lg transition font-medium"
            >
              Monitoring
            </Link>
            <Link
              to="/deployments"
              className="px-4 py-2 bg-bg-hover hover:bg-border text-text-primary rounded-lg transition"
            >
              View Deployments
            </Link>
            <Link
              to="/deploy/new"
              className="px-4 py-2 bg-bg-hover hover:bg-border text-text-primary rounded-lg transition"
            >
              + New Deployment
            </Link>
          </div>
        </div>

        {user && (
          <div className="bg-bg-card rounded-lg shadow overflow-hidden mb-6">
            <div className="px-4 py-5 sm:px-6 border-b border-border">
              <h3 className="text-lg leading-6 font-medium text-text-primary">User Information</h3>
            </div>
            <div className="px-4 py-5 sm:p-6">
              <dl className="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-2">
                <div className="sm:col-span-1">
                  <dt className="text-sm font-medium text-text-secondary">User ID</dt>
                  <dd className="mt-1 text-sm text-text-primary">{user.id}</dd>
                </div>
                <div className="sm:col-span-1">
                  <dt className="text-sm font-medium text-text-secondary">Email</dt>
                  <dd className="mt-1 text-sm text-text-primary">{user.email}</dd>
                </div>
                <div className="sm:col-span-1">
                  <dt className="text-sm font-medium text-text-secondary">Name</dt>
                  <dd className="mt-1 text-sm text-text-primary">{user.name}</dd>
                </div>
                <div className="sm:col-span-1">
                  <dt className="text-sm font-medium text-text-secondary">OAuth Provider</dt>
                  <dd className="mt-1 text-sm text-text-primary">{user.oauth_provider || 'Email/Password'}</dd>
                </div>
              </dl>
            </div>
          </div>
        )}

        <div className="bg-bg-card rounded-lg shadow overflow-hidden">
          <div className="px-4 py-5 sm:px-6 border-b border-border">
            <h3 className="text-lg leading-6 font-medium text-text-primary">Tokens</h3>
          </div>
          <div className="px-4 py-5 sm:p-6 space-y-4">
            <div>
              <dt className="text-sm font-medium text-text-secondary mb-1">Access Token</dt>
              <dd className="text-xs text-text-muted break-all bg-bg-input p-2 rounded">
                {accessToken}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-text-secondary mb-1">Refresh Token</dt>
              <dd className="text-xs text-text-muted break-all bg-bg-input p-2 rounded">
                {refreshToken}
              </dd>
            </div>
            <button
              onClick={refreshAccessToken}
              className="mt-4 px-4 py-2 bg-accent-white text-black hover:bg-accent-light rounded-md text-sm font-medium"
            >
              Refresh Access Token
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
