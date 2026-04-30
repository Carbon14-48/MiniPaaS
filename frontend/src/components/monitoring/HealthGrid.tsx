import { motion } from 'framer-motion';
import { Activity, CheckCircle, XCircle, AlertTriangle, Clock } from 'lucide-react';
import type { ContainerStatus } from '../../lib/monitoringApi';

interface HealthGridProps {
  containers: ContainerStatus[];
  loading: boolean;
  selectedApp: string | null;
  onSelectApp: (appId: string) => void;
}

export default function HealthGrid({
  containers,
  loading,
  selectedApp,
  onSelectApp,
}: HealthGridProps) {
  const statusConfig = {
    running: {
      color: 'accent-green',
      bg: 'bg-accent-green/10',
      icon: CheckCircle,
      label: 'Healthy',
      pulse: true,
    },
    exited: {
      color: 'accent-red',
      bg: 'bg-accent-red/10',
      icon: XCircle,
      label: 'Stopped',
      pulse: false,
    },
    paused: {
      color: 'accent-orange',
      bg: 'bg-accent-orange/10',
      icon: AlertTriangle,
      label: 'Paused',
      pulse: false,
    },
    unknown: {
      color: 'text-muted',
      bg: 'bg-border',
      icon: Clock,
      label: 'Unknown',
      pulse: false,
    },
  };

  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="card p-4">
            <div className="h-20 skeleton rounded-lg" />
          </div>
        ))}
      </div>
    );
  }

  if (containers.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="card p-8 flex flex-col items-center justify-center"
      >
        <Activity className="w-12 h-12 text-text-muted mb-4" />
        <p className="text-text-secondary text-center">No containers running</p>
        <p className="text-text-muted text-sm text-center mt-1">
          Deploy an app to start monitoring
        </p>
      </motion.div>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
      {containers.map((container, index) => {
        const config =
          statusConfig[container.status as keyof typeof statusConfig] || statusConfig.unknown;
        const Icon = config.icon;
        const isSelected = selectedApp === container.app_id;

        return (
          <motion.div
            key={container.container_id || container.app_id}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.05 }}
            onClick={() => onSelectApp(container.app_id)}
            className={`card p-4 cursor-pointer transition-all duration-300 group ${
              isSelected
                ? 'ring-2 ring-accent-blue shadow-glow-blue border-accent-blue/50'
                : 'hover:border-accent-blue/30 hover:shadow-card-hover'
            }`}
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <motion.div
                  animate={
                    config.pulse
                      ? { scale: [1, 1.2, 1], opacity: [1, 0.5, 1] }
                      : {}
                  }
                  transition={{
                    duration: 2,
                    repeat: config.pulse ? Infinity : 0,
                    ease: 'easeInOut',
                  }}
                  className={`w-3 h-3 rounded-full bg-${config.color} ${
                    config.pulse ? 'shadow-glow-' + config.color.split('-')[1] : ''
                  }`}
                />
                <h4 className="font-medium text-text-primary truncate">
                  {container.app_id}
                </h4>
              </div>
              <Icon
                className={`w-4 h-4 text-${config.color} ${
                  config.pulse ? 'animate-pulse' : ''
                }`}
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-text-muted text-xs">Status</span>
                <span className={`text-${config.color} text-xs font-medium`}>
                  {config.label}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-text-muted text-xs">Container</span>
                <span className="text-text-secondary text-xs font-mono truncate max-w-[120px]">
                  {container.container_id?.slice(0, 12)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-text-muted text-xs">User ID</span>
                <span className="text-text-secondary text-xs">{container.user_id}</span>
              </div>
            </div>

            <div
              className={`mt-3 pt-3 border-t border-border/50 flex items-center justify-center gap-2 text-${config.color} text-xs font-medium opacity-0 group-hover:opacity-100 transition-opacity`}
            >
              <Activity className="w-3 h-3" />
              <span>View Details</span>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}