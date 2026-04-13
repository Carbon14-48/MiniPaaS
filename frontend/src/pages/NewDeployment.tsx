import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { deployerApiService, GitHubBranch } from '../lib/api';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';

export default function NewDeployment() {
  const { accessToken } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [repoUrl, setRepoUrl] = useState(searchParams.get('repo') || '');
  const [appName, setAppName] = useState(searchParams.get('name') || '');
  const [branch, setBranch] = useState(searchParams.get('branch') || 'main');
  const [branches, setBranches] = useState<GitHubBranch[]>([]);
  const [branchesLoading, setBranchesLoading] = useState(false);
  const [deploying, setDeploying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (repoUrl && accessToken) {
      const parts = repoUrl.replace('https://github.com/', '').split('/');
      if (parts.length >= 2) {
        const owner = parts[0];
        const repo = parts[1].replace('.git', '');
        loadBranches(owner, repo);
      }
    }
  }, [repoUrl, accessToken]);

  const loadBranches = async (owner: string, repo: string) => {
    if (!accessToken) return;
    try {
      setBranchesLoading(true);
      const data = await deployerApiService.getBranches(accessToken, owner, repo);
      setBranches(data);
      const defaultBranch = data.find((b) => b.name === 'main') || data.find((b) => b.name === 'master');
      if (defaultBranch) {
        setBranch(defaultBranch.name);
      }
    } catch (err) {
      console.error('Failed to load branches:', err);
    } finally {
      setBranchesLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!accessToken) return;

    if (!repoUrl || !appName || !branch) {
      setError('All fields are required');
      return;
    }

    try {
      setDeploying(true);
      setError(null);
      await deployerApiService.createDeployment(accessToken, {
        repo_url: repoUrl,
        branch: branch,
        app_name: appName.toLowerCase().replace(/[^a-z0-9-]/g, '-'),
      });
      navigate(`/deployments`);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to create deployment');
      console.error(err);
    } finally {
      setDeploying(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <nav className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link to="/dashboard" className="text-xl font-bold text-white">MiniPaaS</Link>
            <div className="flex gap-4">
              <Link to="/dashboard" className="text-gray-300 hover:text-white transition">Dashboard</Link>
              <Link to="/deployments" className="text-gray-300 hover:text-white transition">Deployments</Link>
              <Link to="/repos" className="text-white font-medium">New Deployment</Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-2xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold mb-2">Create New Deployment</h1>
        <p className="text-gray-400 mb-8">Deploy your application from GitHub</p>

        {error && (
          <div className="mb-6 p-4 bg-red-900/50 border border-red-700 rounded-lg text-red-300">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Repository URL
            </label>
            <input
              type="text"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="https://github.com/username/repository"
              className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-green-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              App Name
            </label>
            <input
              type="text"
              value={appName}
              onChange={(e) => setAppName(e.target.value)}
              placeholder="my-awesome-app"
              className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-green-500"
              required
            />
            <p className="mt-1 text-sm text-gray-500">
              Only lowercase letters, numbers, and hyphens allowed
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Branch
            </label>
            {branchesLoading ? (
              <div className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-400">
                Loading branches...
              </div>
            ) : branches.length > 0 ? (
              <select
                value={branch}
                onChange={(e) => setBranch(e.target.value)}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-green-500"
              >
                {branches.map((b) => (
                  <option key={b.name} value={b.name}>
                    {b.name} {b.protected ? '(protected)' : ''}
                  </option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                value={branch}
                onChange={(e) => setBranch(e.target.value)}
                placeholder="main"
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-green-500"
                required
              />
            )}
          </div>

          <div className="pt-4">
            <button
              type="submit"
              disabled={deploying}
              className="w-full px-4 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-medium rounded-lg transition"
            >
              {deploying ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-white"></span>
                  Creating Deployment...
                </span>
              ) : (
                'Create Deployment'
              )}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
