import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { deployerApiService, GitHubRepo } from '../lib/api';
import RepoCard from '../components/ui/RepoCard';
import { useNavigate, Link } from 'react-router-dom';

export default function Repositories() {
  const { accessToken } = useAuth();
  const navigate = useNavigate();
  const [repos, setRepos] = useState<GitHubRepo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadRepos();
  }, [accessToken]);

  const loadRepos = async () => {
    if (!accessToken) return;
    try {
      setLoading(true);
      setError(null);
      const data = await deployerApiService.getRepos(accessToken);
      setRepos(data);
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError('GitHub authorization expired. Please login with GitHub again.');
      } else {
        setError('Failed to load repositories');
      }
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeploy = (repo: GitHubRepo) => {
    navigate(`/deploy/new?repo=${encodeURIComponent(repo.html_url)}&name=${encodeURIComponent(repo.name)}&branch=${encodeURIComponent(repo.default_branch)}`);
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
              <Link to="/repos" className="text-white font-medium">Repositories</Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold">Your GitHub Repositories</h1>
          <p className="text-gray-400 mt-1">Select a repository to deploy</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-900/50 border border-red-700 rounded-lg text-red-300">
            {error}
            <button
              onClick={loadRepos}
              className="ml-4 underline hover:no-underline"
            >
              Try again
            </button>
          </div>
        )}

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-green-500"></div>
          </div>
        ) : repos.length === 0 ? (
          <div className="text-center py-12 bg-gray-800 rounded-lg border border-gray-700">
            <p className="text-gray-400 mb-4">No repositories found</p>
            <p className="text-gray-500 text-sm">Make sure you've connected your GitHub account</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {repos.map((repo) => (
              <RepoCard key={repo.id} repo={repo} onDeploy={handleDeploy} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
