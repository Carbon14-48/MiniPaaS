import { GitHubRepo } from '../../lib/api';

interface RepoCardProps {
  repo: GitHubRepo;
  onDeploy: (repo: GitHubRepo) => void;
}

export default function RepoCard({ repo, onDeploy }: RepoCardProps) {
  return (
    <div className="bg-bg-card rounded-lg p-4 border border-border hover:border-border-hover transition">
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold text-text-primary truncate">{repo.name}</h3>
            {repo.private && (
              <span className="px-2 py-0.5 text-xs bg-accent-dark text-text-secondary rounded">
                Private
              </span>
            )}
          </div>
          <p className="text-sm text-text-secondary truncate">{repo.full_name}</p>
        </div>
      </div>

      {repo.description && (
        <p className="text-sm text-text-secondary mb-3 line-clamp-2">{repo.description}</p>
      )}

      <div className="flex items-center gap-4 text-sm text-text-secondary mb-3">
        {repo.language && (
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-accent-gray"></span>
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
          className="px-3 py-1.5 bg-bg-hover hover:bg-border text-text-primary text-sm rounded transition flex-1 text-center"
        >
          View on GitHub
        </a>
        <button
          onClick={() => onDeploy(repo)}
          className="px-3 py-1.5 bg-accent-white text-black hover:bg-accent-light text-sm rounded transition flex-1"
        >
          Deploy
        </button>
      </div>
    </div>
  );
}
