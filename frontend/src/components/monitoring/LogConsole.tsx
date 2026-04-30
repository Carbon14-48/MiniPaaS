import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, Pause, Download, Search, Filter } from 'lucide-react';
import type { LogEntry } from '../../lib/monitoringApi';

interface LogConsoleProps {
  logs: LogEntry[];
  loading: boolean;
  appId: string;
  onFetchLive: () => void;
}

const levelConfig = {
  INFO: { color: 'accent-green', bg: 'bg-accent-green/10', label: 'INFO' },
  WARN: { color: 'accent-orange', bg: 'bg-accent-orange/10', label: 'WARN' },
  ERROR: { color: 'accent-red', bg: 'bg-accent-red/10', label: 'ERROR' },
  DEBUG: { color: 'text-muted', bg: 'bg-border', label: 'DEBUG' },
};

export default function LogConsole({ logs, loading, appId, onFetchLive }: LogConsoleProps) {
  const [isLive, setIsLive] = useState(false);
  const [filter, setFilter] = useState<string>('all');
  const [search, setSearch] = useState('');
  const [autoScroll, setAutoScroll] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isLive) return;
    const interval = setInterval(async () => {
      try {
        await onFetchLive();
      } catch {
        setIsLive(false);
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [isLive, onFetchLive]);

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const filteredLogs = logs.filter((log) => {
    if (filter !== 'all' && log.level !== filter) return false;
    if (search && !log.message.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const handleDownload = () => {
    const content = filteredLogs
      .map((l) => `[${l.level}] ${new Date(l.log_timestamp).toISOString()} ${l.message}`)
      .join('\n');
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${appId}-logs-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="card overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border bg-bg-primary">
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-semibold text-text-primary">Console</h3>
          <span className="text-text-muted text-sm">
            {filteredLogs.length} entries
          </span>
          {isLive && (
            <motion.span
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              className="px-2 py-0.5 text-xs font-medium rounded-full bg-accent-green/20 text-accent-green"
            >
              LIVE
            </motion.span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setFilter(filter === 'all' ? 'ERROR' : filter === 'ERROR' ? 'WARN' : 'all')}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
              filter !== 'all'
                ? 'bg-accent-orange/20 text-accent-orange'
                : 'bg-bg-hover text-text-secondary hover:text-text-primary'
            }`}
          >
            <Filter className="w-3 h-3 inline mr-1" />
            {filter === 'all' ? 'All' : filter}
          </button>
          <button
            onClick={() => setIsLive(!isLive)}
            className={`p-2 rounded-lg transition-colors ${
              isLive
                ? 'bg-accent-green/20 text-accent-green'
                : 'bg-bg-hover text-text-secondary hover:text-text-primary'
            }`}
            title={isLive ? 'Pause live' : 'Start live'}
          >
            {isLive ? (
              <Pause className="w-4 h-4" />
            ) : (
              <Play className="w-4 h-4" />
            )}
          </button>
          <button
            onClick={handleDownload}
            className="p-2 rounded-lg bg-bg-hover text-text-secondary hover:text-text-primary transition-colors"
            title="Download logs"
          >
            <Download className="w-4 h-4" />
          </button>
          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
              autoScroll
                ? 'bg-accent-blue/20 text-accent-blue'
                : 'bg-bg-hover text-text-secondary'
            }`}
          >
            Auto-scroll
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="p-4 border-b border-border">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search logs..."
            className="input pl-10"
          />
        </div>
      </div>

      {/* Log entries */}
      <div
        ref={scrollRef}
        className="h-80 overflow-auto p-4 terminal-bg font-mono text-sm"
      >
        {loading ? (
          <div className="space-y-2">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-5 skeleton rounded w-full" />
            ))}
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="text-text-muted text-center py-8">
            No logs to display
          </div>
        ) : (
          <AnimatePresence>
            {filteredLogs.map((log, i) => {
              const config = levelConfig[log.level] || levelConfig.INFO;
              return (
                <motion.div
                  key={log.id || i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0 }}
                  className={`flex gap-3 py-1 px-2 rounded ${
                    log.level === 'ERROR'
                      ? 'bg-accent-red/5 hover:bg-accent-red/10'
                      : log.level === 'WARN'
                      ? 'bg-accent-orange/5 hover:bg-accent-orange/10'
                      : 'hover:bg-bg-hover'
                  }`}
                >
                  <span className="text-text-muted text-xs shrink-0 w-16">
                    {new Date(log.log_timestamp).toLocaleTimeString()}
                  </span>
                  <span
                    className={`px-1.5 py-0.5 text-xs font-bold rounded ${
                      config.bg + ' text-' + config.color
                    }`}
                  >
                    {config.label}
                  </span>
                  <span className="text-text-primary flex-1 break-all">
                    {log.message}
                  </span>
                </motion.div>
              );
            })}
          </AnimatePresence>
        )}
      </div>
    </motion.div>
  );
}