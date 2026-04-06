import type { ReactNode } from 'react';
import Lightning from '../ui/Lightning';

type AuthBackgroundProps = {
  children: ReactNode;
};

export default function AuthBackground({ children }: AuthBackgroundProps) {
  return (
    <div className="relative min-h-screen overflow-hidden bg-gray-950">
      <div className="pointer-events-none absolute inset-0">
        <Lightning
          hue={360}
          xOffset={0}
          speed={1}
          intensity={1}
          size={1}
        />
      </div>
      <div className="relative z-10">{children}</div>
    </div>
  );
}
