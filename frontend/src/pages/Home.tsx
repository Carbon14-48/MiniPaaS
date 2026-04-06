import { Link } from 'react-router-dom';
import AuthBackground from '../components/layout/AuthBackground';

export default function Home() {
  return (
    <AuthBackground>
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="max-w-md w-full text-center backdrop-blur-sm bg-gray-950/40 border border-gray-700/60 rounded-xl p-8">
          <h1 className="text-4xl font-extrabold text-white mb-4">MiniPaaS</h1>
          <p className="text-xl text-gray-300 mb-8">Lightweight Platform-as-a-Service</p>

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

          <div className="mt-12 text-gray-300 text-sm">
            Auth Service running at localhost:8001
          </div>
        </div>
      </div>
    </AuthBackground>
  );
}
