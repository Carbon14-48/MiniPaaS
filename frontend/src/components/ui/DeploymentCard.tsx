import { Deployment } from '../../lib/api';

interface DeploymentCardProps {
  deployment: Deployment;
  onStop?: (id: string) => void;
  onStart?: (id: string) => void;
  onRestart?: (id: string) => void;
  onDelete?: (id: string) => void;
  onViewLogs?: (id: string) => void;
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
    running: 'bg-green-500',
    stopped: 'bg-gray-500',
    building: 'bg-yellow-500',
    deploying: 'bg-blue-500',
    pending: 'bg-gray-400',
    failed: 'bg-red-500',
    blocked: 'bg-red-700',
  };

  const statusTextColors: Record<string, string> = {
    running: 'text-green-400',
    stopped: 'text-gray-400',
    building: 'text-yellow-400',
    deploying: 'text-blue-400',
    pending: 'text-gray-400',
    failed: 'text-red-400',
    blocked: 'text-red-600',
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
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-lg font-semibold text-white">{deployment.app_name}</h3>
          <p className="text-sm text-gray-400">
            {deployment.repo_url.split('/').slice(-2).join('/')}
          </p>
        </div>
        <span
          className={`px-3 py-1 rounded-full text-xs font-medium text-white ${statusColors[deployment.status] || 'bg-gray-500'}`}
        >
          {deployment.status.toUpperCase()}
        </span>
      </div>

      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-400">Branch:</span>
          <span className="text-white">{deployment.branch}</span>
        </div>
        {deployment.host_port && (
          <div className="flex justify-between">
            <span className="text-gray-400">URL:</span>
            <a
              href={deployment.container_url || `http://localhost:${deployment.host_port}`}
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
            <span className="text-gray-400">Image:</span>
            <span className="text-gray-300 text-xs font-mono truncate max-w-[200px]">
              {deployment.image_tag}
            </span>
          </div>
        )}
        <div className="flex justify-between">
          <span className="text-gray-400">Created:</span>
          <span className="text-gray-300">{formatDate(deployment.created_at)}</span>
        </div>
        {deployment.started_at && (
          <div className="flex justify-between">
            <span className="text-gray-400">Started:</span>
            <span className="text-gray-300">{formatDate(deployment.started_at)}</span>
          </div>
        )}
      </div>

      {deployment.error_message && (
        <div className="mt-3 p-3 bg-red-900/50 rounded text-red-300 text-sm">
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
            className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-sm rounded transition"
          >
            Stop
          </button>
        )}
        {(deployment.status === 'stopped' || deployment.status === 'failed') && onStart && (
          <button
            onClick={() => onStart(deployment.id)}
            className="px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white text-sm rounded transition"
          >
            Start
          </button>
        )}
        {deployment.status === 'running' && onRestart && (
          <button
            onClick={() => onRestart(deployment.id)}
            className="px-3 py-1.5 bg-yellow-600 hover:bg-yellow-700 text-white text-sm rounded transition"
          >
            Restart
          </button>
        )}
        {onViewLogs && (
          <button
            onClick={() => onViewLogs(deployment.id)}
            className="px-3 py-1.5 bg-gray-600 hover:bg-gray-700 text-white text-sm rounded transition"
          >
            Logs
          </button>
        )}
        {onDelete && (
          <button
            onClick={() => onDelete(deployment.id)}
            className="px-3 py-1.5 bg-red-900 hover:bg-red-950 text-red-300 text-sm rounded transition"
          >
            Delete
          </button>
        )}
      </div>
    </div>
  );
}
