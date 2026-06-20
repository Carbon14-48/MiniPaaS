interface StatusBadgeProps {
  status: string;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const statusConfig: Record<string, { color: string; label: string }> = {
    running: { color: 'bg-accent-white', label: 'Running' },
    stopped: { color: 'bg-accent-dark', label: 'Stopped' },
    building: { color: 'bg-accent-gray animate-pulse', label: 'Building' },
    deploying: { color: 'bg-accent-gray animate-pulse', label: 'Deploying' },
    pending: { color: 'bg-accent-dark', label: 'Pending' },
    failed: { color: 'bg-accent-red', label: 'Failed' },
    blocked: { color: 'bg-accent-red', label: 'Blocked' },
  };

  const config = statusConfig[status] || { color: 'bg-accent-dark', label: status };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium text-white ${config.color}`}>
      <span className="relative flex h-2 w-2 mr-1.5">
        {status === 'building' || status === 'deploying' ? (
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
        ) : null}
        <span className={`relative inline-flex rounded-full h-2 w-2 ${config.color}`}></span>
      </span>
      {config.label}
    </span>
  );
}
