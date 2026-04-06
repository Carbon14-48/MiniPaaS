import { useAuth } from '../context/AuthContext';

export default function Dashboard() {
  const { user, logout, refreshAccessToken, accessToken, refreshToken } = useAuth();

  return (
    <div className="min-h-screen bg-gray-900">
      <nav className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <span className="text-xl font-bold text-white">MiniPaaS</span>
            </div>
            <button
              onClick={logout}
              className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md"
            >
              Logout
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8 px-4">
        <h1 className="text-2xl font-bold text-white mb-6">Dashboard</h1>

        {user && (
          <div className="bg-gray-800 rounded-lg shadow overflow-hidden">
            <div className="px-4 py-5 sm:px-6 border-b border-gray-700">
              <h3 className="text-lg leading-6 font-medium text-white">User Information</h3>
            </div>
            <div className="px-4 py-5 sm:p-6">
              <dl className="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-2">
                <div className="sm:col-span-1">
                  <dt className="text-sm font-medium text-gray-400">User ID</dt>
                  <dd className="mt-1 text-sm text-white">{user.id}</dd>
                </div>
                <div className="sm:col-span-1">
                  <dt className="text-sm font-medium text-gray-400">Email</dt>
                  <dd className="mt-1 text-sm text-white">{user.email}</dd>
                </div>
                <div className="sm:col-span-1">
                  <dt className="text-sm font-medium text-gray-400">Name</dt>
                  <dd className="mt-1 text-sm text-white">{user.name}</dd>
                </div>
                <div className="sm:col-span-1">
                  <dt className="text-sm font-medium text-gray-400">OAuth Provider</dt>
                  <dd className="mt-1 text-sm text-white">{user.oauth_provider || 'Email/Password'}</dd>
                </div>
                <div className="sm:col-span-1">
                  <dt className="text-sm font-medium text-gray-400">Has Password</dt>
                  <dd className="mt-1 text-sm text-white">{user.has_password ? 'Yes' : 'No'}</dd>
                </div>
              </dl>
            </div>
          </div>
        )}

        <div className="mt-6 bg-gray-800 rounded-lg shadow overflow-hidden">
          <div className="px-4 py-5 sm:px-6 border-b border-gray-700">
            <h3 className="text-lg leading-6 font-medium text-white">Tokens</h3>
          </div>
          <div className="px-4 py-5 sm:p-6 space-y-4">
            <div>
              <dt className="text-sm font-medium text-gray-400 mb-1">Access Token</dt>
              <dd className="text-xs text-gray-500 break-all bg-gray-900 p-2 rounded">
                {accessToken}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-400 mb-1">Refresh Token</dt>
              <dd className="text-xs text-gray-500 break-all bg-gray-900 p-2 rounded">
                {refreshToken}
              </dd>
            </div>
            <button
              onClick={refreshAccessToken}
              className="mt-4 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md text-sm font-medium"
            >
              Refresh Access Token
            </button>
          </div>
        </div>

        <div className="mt-6 bg-gray-800 rounded-lg shadow overflow-hidden">
          <div className="px-4 py-5 sm:px-6 border-b border-gray-700">
            <h3 className="text-lg leading-6 font-medium text-white">Quick Test</h3>
          </div>
          <div className="px-4 py-5 sm:p-6">
            <p className="text-sm text-gray-400 mb-4">
              Try refreshing the page - your session should persist (tokens are stored in localStorage).
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium"
            >
              Reload Page
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
