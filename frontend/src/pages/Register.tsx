import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import AuthBackground from '../components/layout/AuthBackground';

export default function Register() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { register, isLoading, error } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await register(email, password, name);
      navigate('/dashboard');
    } catch {
      // Error handled by context
    }
  };

  return (
    <AuthBackground>
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-text-primary">
            Create your MiniPaaS account
          </h2>
          <p className="mt-2 text-center text-sm text-text-secondary">
            Already have an account?{' '}
            <Link to="/login" className="font-medium text-text-secondary hover:text-text-primary">
              Sign in
            </Link>
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-accent-red/10 border border-accent-red/30 rounded p-3 text-accent-red text-sm">
              {error}
            </div>
          )}

          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Full name"
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-border placeholder-text-muted text-text-primary bg-bg-input rounded-t-md focus:outline-none focus:ring-2 focus:ring-accent-white/30 focus:border-accent-white focus:z-10 sm:text-sm"
              />
            </div>
            <div>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email address"
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-border placeholder-text-muted text-text-primary bg-bg-input focus:outline-none focus:ring-2 focus:ring-accent-white/30 focus:border-accent-white focus:z-10 sm:text-sm"
              />
            </div>
            <div>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-border placeholder-text-muted text-text-primary bg-bg-input rounded-b-md focus:outline-none focus:ring-2 focus:ring-accent-white/30 focus:border-accent-white focus:z-10 sm:text-sm"
              />
            </div>
          </div>

          <div className="text-xs text-text-muted">
            Password must be at least 8 characters with uppercase, lowercase, and digit.
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-black bg-accent-white hover:bg-accent-light focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent-white disabled:opacity-50"
          >
            {isLoading ? 'Creating account...' : 'Create account'}
          </button>
        </form>
      </div>
    </div>
    </AuthBackground>
  );
}
