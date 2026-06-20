import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function GitHubCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { completeGitHubLogin } = useAuth();
  const code = searchParams.get('code');

  useEffect(() => {
    if (!code) {
      navigate('/login');
      return;
    }

    const handleCallback = async () => {
      try {
        await completeGitHubLogin(code);
        navigate('/dashboard');
      } catch (error) {
        console.error('GitHub OAuth failed:', error);
        navigate('/login?error=github_auth_failed');
      }
    };

    handleCallback();
  }, [code, navigate, completeGitHubLogin]);

  return (
    <div className="min-h-screen bg-bg-primary flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-white mx-auto mb-4"></div>
        <p className="text-text-primary text-lg">Authenticating with GitHub...</p>
      </div>
    </div>
  );
}
