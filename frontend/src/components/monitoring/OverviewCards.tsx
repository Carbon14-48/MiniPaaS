import { motion } from 'framer-motion';
import { Server, Cpu, HardDrive, AlertCircle } from 'lucide-react';

interface OverviewCardsProps {
  apps: {
    status: string;
    cpu_percent?: number;
    memory_percent?: number;
  }[];
  loading: boolean;
}

function thresholdColor(value: number, over80: string, over50: string, under: string): string {
  return value > 80 ? over80 : value > 50 ? over50 : under;
}

function thresholdGradient(value: number, over80: string, over50: string, under: string): string {
  const color = thresholdColor(value, over80, over50, under);
  return `from-${color}/20`;
}

export default function OverviewCards({ apps, loading }: OverviewCardsProps) {
  const runningApps = apps.filter((a) => a.status === 'running').length;
  const avgCpu =
    apps.length > 0
      ? apps.reduce((acc, a) => acc + (a.cpu_percent || 0), 0) / apps.length
      : 0;
  const avgRam =
    apps.length > 0
      ? apps.reduce((acc, a) => acc + (a.memory_percent || 0), 0) / apps.length
      : 0;
  const alerts = apps.filter((a) => (a.cpu_percent ?? 0) > 80 || (a.memory_percent ?? 0) > 80).length;

  const cards = [
    {
      label: 'Active Apps',
      value: runningApps,
      icon: Server,
      color: 'accent-green',
      gradient: 'from-accent-green/20 to-transparent',
    },
    {
      label: 'Avg CPU',
      value: `${avgCpu.toFixed(1)}%`,
      icon: Cpu,
      color: thresholdColor(avgCpu, 'accent-red', 'accent-orange', 'accent-blue'),
      gradient: thresholdGradient(avgCpu, 'accent-red', 'accent-orange', 'accent-blue'),
    },
    {
      label: 'Avg RAM',
      value: `${avgRam.toFixed(1)}%`,
      icon: HardDrive,
      color: thresholdColor(avgRam, 'accent-red', 'accent-orange', 'accent-purple'),
      gradient: thresholdGradient(avgRam, 'accent-red', 'accent-orange', 'accent-purple'),
    },
    {
      label: 'Alerts',
      value: alerts,
      icon: AlertCircle,
      color: alerts > 0 ? 'accent-red' : 'text-muted',
      gradient: alerts > 0 ? 'from-accent-red/20 to-transparent' : 'from-border/20 to-transparent',
    },
  ];

  return (
    <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
      {cards.map((card, index) => (
        <motion.div
          key={card.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1, duration: 0.4 }}
          className={`card relative overflow-hidden p-5 group cursor-default`}
        >
          <div
            className={`absolute inset-0 bg-gradient-to-br ${card.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-500`}
          />
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-3">
              <span className="text-text-secondary text-sm font-medium">
                {card.label}
              </span>
              <card.icon
                className={`w-5 h-5 text-${card.color} transition-transform duration-300 group-hover:scale-110`}
              />
            </div>
            {loading ? (
              <div className="h-8 w-16 skeleton rounded" />
            ) : (
              <motion.div
                initial={{ scale: 0.8 }}
                animate={{ scale: 1 }}
                className={`text-3xl font-bold text-${card.color}`}
              >
                {card.value}
              </motion.div>
            )}
          </div>
          <div
            className={`absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-${card.color} to-transparent transform origin-left scale-x-0 group-hover:scale-x-100 transition-transform duration-500`}
          />
        </motion.div>
      ))}
    </div>
  );
}
