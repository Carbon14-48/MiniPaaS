interface StatusBadgeProps {
  status: string;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const statusConfig: Record<string, { color: string; label: string }> = {
    running: { color: 'bg-green-500', label: 'Running' },
    stopped: { color: 'bg-gray-500', label: 'Stopped' },
    building: { color: 'bg-yellow-500 animate-pulse', label: 'Building' },
    deploying: { color: 'bg-blue-500 animate-pulse', label: 'Deploying' },
    pending: { color: 'bg-gray-400', label: 'Pending' },
    failed: { color: 'bg-red-500', label: 'Failed' },
    blocked: { color: 'bg-red-700', label: 'Blocked' },
  };

  const config = statusConfig[status] || { color: 'bg-gray-500', label: status };

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
