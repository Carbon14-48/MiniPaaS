import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  Activity,
  Server,
  FileText,
  Settings,
  RefreshCw,
  Search,
  ChevronRight,
  LayoutDashboard,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { monitoringApiService, type Metric, type LogEntry, type ContainerStatus } from '../lib/monitoringApi';
import OverviewCards from '../components/monitoring/OverviewCards';
import AppCharts from '../components/monitoring/AppCharts';
import LogConsole from '../components/monitoring/LogConsole';
import HealthGrid from '../components/monitoring/HealthGrid';

type Tab = 'metrics' | 'logs' | 'health';

export default function Monitoring() {
  const { user, accessToken, logout } = useAuth();

  const [selectedApp, setSelectedApp] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('metrics');
  const [summary, setSummary] = useState<Metric[]>([]);
  const [appMetrics, setAppMetrics] = useState<Metric[]>([]);
  const [appLogs, setAppLogs] = useState<LogEntry[]>([]);
  const [containers, setContainers] = useState<ContainerStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [sidebarSearch, setSidebarSearch] = useState('');

  const userId = user?.id;
  const uniqueApps = Array.from(
    new Set(summary.filter(m => m.user_id === userId).map((m) => m.app_id))
  ).filter((app) =>
    app.toLowerCase().includes(sidebarSearch.toLowerCase())
  );

const fetchData = useCallback(async () => {
    if (!accessToken) return;
    setLoading(true);
    try {
      const summaryData = await monitoringApiService.getSummary();
      setSummary(summaryData || []);

      try {
        const containersData = await monitoringApiService.getAllContainers();
        setContainers(containersData.containers || []);
      } catch (e) {
        setContainers([]);
      }

      if (!selectedApp && summaryData && summaryData.length > 0) {
        const userApps = summaryData.filter(m => m.user_id === userId);
        if (userApps.length > 0) {
          setSelectedApp(userApps[0].app_id);
        }
      }
    } catch (err) {
      // Ignore
    } finally {
      setLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  useEffect(() => {
    if (!selectedApp) return;
    const fetchAppData = async () => {
      try {
        const [metricsData, logsData] = await Promise.all([
          monitoringApiService.getAppMetrics(selectedApp),
          monitoringApiService.getAppLogs(selectedApp),
        ]);
        setAppMetrics(metricsData || []);
        setAppLogs(logsData || []);
      } catch (err) {
        // Ignore
      }
    };
    fetchAppData();
    const interval = setInterval(fetchAppData, 30000);
    return () => clearInterval(interval);
  }, [selectedApp]);

  // Refresh app data when summary changes (new app added)
  useEffect(() => {
    if (!selectedApp || summary.length === 0) return;
    const appExists = summary.some(m => m.app_id === selectedApp);
    if (appExists && selectedApp) {
      // Refresh metrics and logs for selected app
      monitoringApiService.getAppMetrics(selectedApp).then(setAppMetrics).catch(() => {});
      monitoringApiService.getAppLogs(selectedApp).then(setAppLogs).catch(() => {});
    }
  }, [summary, selectedApp]);

  const handleLiveLogs = async () => {
    if (!selectedApp) return;
    try {
      const liveData = await monitoringApiService.getLiveLogs(selectedApp);
      const newLogs: LogEntry[] = (liveData.entries || []).map((entry, i) => ({
        id: `live-${i}-${Date.now()}`,
        app_id: selectedApp,
        user_id: user?.id || 0,
        level: 'INFO' as const,
        message: entry,
        log_timestamp: new Date().toISOString(),
        collected_at: new Date().toISOString(),
      }));
      setAppLogs((prev) => [...prev, ...newLogs].slice(-500));
    } catch (err) {
      console.error('Failed to fetch live logs:', err);
    }
  };

  const tabs: { id: Tab; label: string; icon: typeof Activity }[] = [
    { id: 'metrics', label: 'Metrics', icon: Activity },
    { id: 'logs', label: 'Logs', icon: FileText },
    { id: 'health', label: 'Health', icon: Server },
  ];

  return (
    <div className="min-h-screen flex bg-bg-primary">
      {/* Sidebar */}
      <motion.aside
        initial={{ x: -20, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        className="w-64 xl:w-72 shrink-0 border-r border-border bg-bg-card/50 backdrop-blur-md flex flex-col"
      >
        {/* Logo */}
        <div className="p-5 border-b border-border">
          <Link
            to="/dashboard"
            className="flex items-center gap-2 text-xl font-bold text-gradient"
          >
            <LayoutDashboard className="w-5 h-5 text-accent-blue" />
            <span className="bg-gradient-to-r from-accent-blue to-accent-cyan bg-clip-text text-transparent">
              MiniPaaS
            </span>
          </Link>
        </div>

        {/* Search */}
        <div className="p-4 border-b border-border">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
            <input
              type="text"
              value={sidebarSearch}
              onChange={(e) => setSidebarSearch(e.target.value)}
              placeholder="Search apps..."
              className="input pl-10 py-2 text-sm"
            />
          </div>
        </div>

        {/* Apps List */}
        <div className="flex-1 overflow-auto p-2">
          <div className="mb-2 px-3 py-1">
            <span className="text-text-muted text-xs font-medium uppercase tracking-wider">
              Your Apps
            </span>
          </div>
          {loading ? (
            <div className="space-y-2 p-2">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-10 skeleton rounded-lg" />
              ))}
            </div>
          ) : uniqueApps.length === 0 ? (
            <div className="px-3 py-8 text-center">
              <p className="text-text-muted text-sm">No apps found</p>
            </div>
          ) : (
            uniqueApps.map((app) => {
              const appData = summary.find((m) => m.app_id === app);
              const isSelected = selectedApp === app;
              return (
                <button
                  key={app}
                  onClick={() => setSelectedApp(app)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-all duration-200 group ${
                    isSelected
                      ? 'bg-accent-blue/10 text-accent-blue border border-accent-blue/30'
                      : 'hover:bg-bg-hover text-text-secondary hover:text-text-primary'
                  }`}
                >
                  <motion.div
                    animate={
                      appData?.status === 'running'
                        ? { scale: [1, 1.2, 1], opacity: [1, 0.6, 1] }
                        : {}
                    }
                    transition={{ duration: 2, repeat: Infinity }}
                    className={`w-2 h-2 rounded-full ${
                      appData?.status === 'running' ? 'bg-accent-green' : 'bg-text-muted'
                    }`}
                  />
                  <span className="flex-1 truncate text-sm font-medium">{app}</span>
                  {isSelected && (
                    <ChevronRight className="w-4 h-4 text-accent-blue" />
                  )}
                </button>
              );
            })
          )}
        </div>

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-border space-y-2">
          <Link
            to="/dashboard"
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-bg-hover transition-colors"
          >
            <LayoutDashboard className="w-4 h-4" />
            <span className="text-sm">Dashboard</span>
          </Link>
          <button
            onClick={logout}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-text-secondary hover:text-accent-red hover:bg-accent-red/10 transition-colors"
          >
            <Settings className="w-4 h-4" />
            <span className="text-sm">Logout</span>
          </button>
        </div>
      </motion.aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="h-16 shrink-0 border-b border-border bg-bg-card/50 backdrop-blur-md px-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-lg font-semibold text-text-primary">Monitoring</h1>
            {selectedApp && (
              <span className="px-3 py-1 text-sm rounded-full bg-accent-blue/10 text-accent-blue border border-accent-blue/20">
                {selectedApp}
              </span>
            )}
          </div>
          <div className="flex items-center gap-3">
            <motion.button
              whileHover={{ rotate: 180 }}
              transition={{ duration: 0.4 }}
              whileTap={{ scale: 0.9 }}
              onClick={fetchData}
              className="p-2 rounded-lg bg-bg-hover text-text-secondary hover:text-text-primary transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
            </motion.button>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-auto p-6">
          <div className="max-w-7xl mx-auto space-y-6">
            {/* Overview Cards */}
            <OverviewCards apps={summary} loading={loading} />

            {/* Tabs */}
            <div className="flex items-center gap-2 border-b border-border">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-accent-blue text-accent-blue'
                      : 'border-transparent text-text-muted hover:text-text-primary'
                  }`}
                >
                  <tab.icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
              >
                {activeTab === 'metrics' && (
                  <AppCharts metrics={appMetrics} loading={loading} />
                )}
                {activeTab === 'logs' && (
                  <LogConsole
                    logs={appLogs}
                    loading={loading}
                    appId={selectedApp || ''}
                    onFetchLive={handleLiveLogs}
                  />
                )}
                {activeTab === 'health' && (
                  <HealthGrid
                    containers={containers}
                    loading={loading}
                    selectedApp={selectedApp}
                    onSelectApp={setSelectedApp}
                  />
                )}
              </motion.div>
            </AnimatePresence>
          </div>
        </main>
      </div>
    </div>
  );
}