import { useState } from 'react';

interface LogViewerProps {
  logs: string;
  source: string;
  onClose: () => void;
}

export default function LogViewer({ logs, source, onClose }: LogViewerProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(logs);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-lg max-w-4xl w-full max-h-[80vh] flex flex-col border border-gray-700">
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <div>
            <h2 className="text-lg font-semibold text-white">Deployment Logs</h2>
            <p className="text-sm text-gray-400">Source: {source}</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleCopy}
              className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded transition"
            >
              {copied ? 'Copied!' : 'Copy'}
            </button>
            <button
              onClick={onClose}
              className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-sm rounded transition"
            >
              Close
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-auto p-4">
          <pre className="text-sm text-green-400 font-mono whitespace-pre-wrap break-all">
            {logs || 'No logs available'}
          </pre>
        </div>
      </div>
    </div>
  );
}
