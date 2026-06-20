import { Deployment } from '../../lib/api';

interface DeploymentCardProps {
  deployment: Deployment;
  onStop?: (id: string) => void;
  onStart?: (id: string) => void;
  onRestart?: (id: string) => void;
  onDelete?: (id: string) => void;
  onViewLogs?: (id: string) => void;
}

function safeUrl(url: string | null | undefined): string {
  if (!url) return '';
  if (url.startsWith('http://') || url.startsWith('https://')) return url;
  return '';
}

export default function DeploymentCard({
  deployment,
  onStop,
  onStart,
  onRestart,
  onDelete,
  onViewLogs,
}: DeploymentCardProps) {
  const statusColors: Record<string, string> = {
    running: 'bg-accent-white',
    stopped: 'bg-accent-dark',
    building: 'bg-accent-gray',
    deploying: 'bg-accent-gray',
    pending: 'bg-accent-dark',
    failed: 'bg-accent-red',
    blocked: 'bg-accent-red',
  };

  const statusTextColors: Record<string, string> = {
    running: 'text-text-primary',
    stopped: 'text-text-muted',
    building: 'text-text-secondary',
    deploying: 'text-text-secondary',
    pending: 'text-text-muted',
    failed: 'text-accent-red',
    blocked: 'text-accent-red',
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="bg-bg-card rounded-lg p-4 border border-border">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-lg font-semibold text-text-primary">{deployment.app_name}</h3>
          <p className="text-sm text-text-secondary">
            {deployment.repo_url.split('/').slice(-2).join('/')}
          </p>
        </div>
        <span
          className={`px-3 py-1 rounded-full text-xs font-medium text-white ${statusColors[deployment.status] || 'bg-accent-dark'}`}
        >
          {deployment.status.toUpperCase()}
        </span>
      </div>

      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-text-secondary">Branch:</span>
          <span className="text-text-primary">{deployment.branch}</span>
        </div>
        {deployment.host_port && (
          <div className="flex justify-between">
            <span className="text-text-secondary">URL:</span>
            <a
              href={safeUrl(deployment.container_url) || `http://localhost:${deployment.host_port}`}
              target="_blank"
              rel="noopener noreferrer"
              className={`${statusTextColors[deployment.status]} hover:underline`}
            >
              {deployment.container_url || `localhost:${deployment.host_port}`}
            </a>
          </div>
        )}
        {deployment.image_tag && (
          <div className="flex justify-between">
            <span className="text-text-secondary">Image:</span>
            <span className="text-text-secondary text-xs font-mono truncate max-w-[200px]">
              {deployment.image_tag}
            </span>
          </div>
        )}
        <div className="flex justify-between">
          <span className="text-text-secondary">Created:</span>
          <span className="text-text-secondary">{formatDate(deployment.created_at)}</span>
        </div>
        {deployment.started_at && (
          <div className="flex justify-between">
            <span className="text-text-secondary">Started:</span>
            <span className="text-text-secondary">{formatDate(deployment.started_at)}</span>
          </div>
        )}
      </div>

      {deployment.error_message && (
        <div className="mt-3 p-3 bg-accent-red/10 border border-accent-red/30 rounded text-accent-red text-sm">
          <div className="font-semibold mb-1">
            {deployment.status === 'blocked' ? 'Blocked by Security Scanner' : 'Error'}
          </div>
          <div className="text-xs">{deployment.error_message}</div>
        </div>
      )}

      <div className="mt-4 flex flex-wrap gap-2">
        {deployment.status === 'running' && onStop && (
          <button
            onClick={() => onStop(deployment.id)}
            className="px-3 py-1.5 bg-transparent border border-accent-red text-accent-red hover:bg-accent-red/10 text-sm rounded transition"
          >
            Stop
          </button>
        )}
        {(deployment.status === 'stopped' || deployment.status === 'failed') && onStart && (
          <button
            onClick={() => onStart(deployment.id)}
            className="px-3 py-1.5 bg-accent-white text-black hover:bg-accent-light text-sm rounded transition"
          >
            Start
          </button>
        )}
        {deployment.status === 'running' && onRestart && (
          <button
            onClick={() => onRestart(deployment.id)}
            className="px-3 py-1.5 bg-transparent border border-accent-gray text-accent-gray hover:bg-accent-gray/10 text-sm rounded transition"
          >
            Restart
          </button>
        )}
        {onViewLogs && (
          <button
            onClick={() => onViewLogs(deployment.id)}
            className="px-3 py-1.5 bg-bg-hover hover:bg-border text-text-primary text-sm rounded transition"
          >
            Logs
          </button>
        )}
        {onDelete && (
          <button
            onClick={() => onDelete(deployment.id)}
            className="px-3 py-1.5 bg-transparent border border-accent-red/50 text-accent-red hover:bg-accent-red/10 text-sm rounded transition"
          >
            Delete
          </button>
        )}
      </div>
    </div>
  );
}
