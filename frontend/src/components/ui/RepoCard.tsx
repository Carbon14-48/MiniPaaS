import { GitHubRepo } from '../../lib/api';

interface RepoCardProps {
  repo: GitHubRepo;
  onDeploy: (repo: GitHubRepo) => void;
}

export default function RepoCard({ repo, onDeploy }: RepoCardProps) {
  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 hover:border-gray-600 transition">
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold text-white truncate">{repo.name}</h3>
            {repo.private && (
              <span className="px-2 py-0.5 text-xs bg-yellow-600 text-yellow-200 rounded">
                Private
              </span>
            )}
          </div>
          <p className="text-sm text-gray-400 truncate">{repo.full_name}</p>
        </div>
      </div>

      {repo.description && (
        <p className="text-sm text-gray-300 mb-3 line-clamp-2">{repo.description}</p>
      )}

      <div className="flex items-center gap-4 text-sm text-gray-400 mb-3">
        {repo.language && (
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-blue-500"></span>
            {repo.language}
          </span>
        )}
        <span>Branch: {repo.default_branch}</span>
      </div>

      <div className="flex gap-2">
        <a
          href={repo.html_url}
          target="_blank"
          rel="noopener noreferrer"
          className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded transition flex-1 text-center"
        >
          View on GitHub
        </a>
        <button
          onClick={() => onDeploy(repo)}
          className="px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white text-sm rounded transition flex-1"
        >
          Deploy
        </button>
      </div>
    </div>
  );
}
