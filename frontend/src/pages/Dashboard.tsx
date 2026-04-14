import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { deployerApiService } from '../lib/api';
import { Link } from 'react-router-dom';

export default function Dashboard() {
  const { user, logout, refreshAccessToken, accessToken, refreshToken } = useAuth();
  const [deployments, setDeployments] = useState<any[]>([]);

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
    <div className="min-h-screen bg-gray-900">
      <nav className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link to="/dashboard" className="text-xl font-bold text-white">MiniPaaS</Link>
            <div className="flex gap-4">
              <Link to="/repos" className="text-gray-300 hover:text-white transition">Repositories</Link>
              <Link to="/deployments" className="text-gray-300 hover:text-white transition">Deployments</Link>
              <Link to="/deploy/new" className="px-4 py-1 bg-green-600 hover:bg-green-700 text-white rounded-lg transition text-sm font-medium">+ New Deploy</Link>
            </div>
          </div>
          <button
            onClick={logout}
            className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md"
          >
            Logout
          </button>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 px-4">
        <h1 className="text-2xl font-bold text-white mb-6">Dashboard</h1>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="text-3xl font-bold text-white">{deployments.length}</div>
            <div className="text-gray-400 text-sm">Total Deployments</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-4 border border-green-700">
            <div className="text-3xl font-bold text-green-400">{runningCount}</div>
            <div className="text-gray-400 text-sm">Running</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-4 border border-yellow-700">
            <div className="text-3xl font-bold text-yellow-400">{buildingCount}</div>
            <div className="text-gray-400 text-sm">Building</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
            <div className="text-3xl font-bold text-gray-400">{stoppedCount}</div>
            <div className="text-gray-400 text-sm">Stopped</div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 mb-6">
          <h2 className="text-lg font-semibold text-white mb-4">Quick Actions</h2>
          <div className="flex gap-4">
            <Link
              to="/repos"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
            >
              Browse Repositories
            </Link>
            <Link
              to="/deployments"
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition"
            >
              View Deployments
            </Link>
            <Link
              to="/deploy/new"
              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition"
            >
              + New Deployment
            </Link>
          </div>
        </div>

        {user && (
          <div className="bg-gray-800 rounded-lg shadow overflow-hidden mb-6">
            <div className="px-4 py-5 sm:px-6 border-b border-gray-700">
              <h3 className="text-lg leading-6 font-medium text-white">User Information</h3>
            </div>
            <div className="px-4 py-5 sm:p-6">
              <dl className="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-2">
                <div className="sm:col-span-1">
                  <dt className="text-sm font-medium text-gray-400">User ID</dt>
                  <dd className="mt-1 text-sm text-white">{user.id}</dd>
                </div>
                <div className="sm:col-span-1">
                  <dt className="text-sm font-medium text-gray-400">Email</dt>
                  <dd className="mt-1 text-sm text-white">{user.email}</dd>
                </div>
                <div className="sm:col-span-1">
                  <dt className="text-sm font-medium text-gray-400">Name</dt>
                  <dd className="mt-1 text-sm text-white">{user.name}</dd>
                </div>
                <div className="sm:col-span-1">
                  <dt className="text-sm font-medium text-gray-400">OAuth Provider</dt>
                  <dd className="mt-1 text-sm text-white">{user.oauth_provider || 'Email/Password'}</dd>
                </div>
              </dl>
            </div>
          </div>
        )}

        <div className="bg-gray-800 rounded-lg shadow overflow-hidden">
          <div className="px-4 py-5 sm:px-6 border-b border-gray-700">
            <h3 className="text-lg leading-6 font-medium text-white">Tokens</h3>
          </div>
          <div className="px-4 py-5 sm:p-6 space-y-4">
            <div>
              <dt className="text-sm font-medium text-gray-400 mb-1">Access Token</dt>
              <dd className="text-xs text-gray-500 break-all bg-gray-900 p-2 rounded">
                {accessToken}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-400 mb-1">Refresh Token</dt>
              <dd className="text-xs text-gray-500 break-all bg-gray-900 p-2 rounded">
                {refreshToken}
              </dd>
            </div>
            <button
              onClick={refreshAccessToken}
              className="mt-4 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md text-sm font-medium"
            >
              Refresh Access Token
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
