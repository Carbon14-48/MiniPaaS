import { Link } from 'react-router-dom';

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        <h1 className="text-4xl font-extrabold text-white mb-4">MiniPaaS</h1>
        <p className="text-xl text-gray-400 mb-8">Lightweight Platform-as-a-Service</p>
        
        <div className="space-y-4">
          <Link
            to="/login"
            className="block w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-md transition"
          >
            Login
          </Link>
          <Link
            to="/register"
            className="block w-full px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white font-medium rounded-md transition"
          >
            Register
          </Link>
        </div>

        <div className="mt-12 text-gray-500 text-sm">
          Auth Service running at localhost:8001
        </div>
      </div>
    </div>
  );
}
