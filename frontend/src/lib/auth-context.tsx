/** Auth context — wraps the app and provides login state. */
'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, getUser, getToken, clearAuth, setToken, setUser as saveUser } from '@/lib/api';
import { useRouter } from 'next/navigation';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  isLoading: true,
  login: () => {},
  logout: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    if (getToken()) {
      setUser(getUser());
    }
    setIsLoading(false);
  }, []);

  const login = (token: string, userData: User) => {
    setToken(token);
    saveUser(userData);
    setUser(userData);
  };

  const logout = () => {
    clearAuth();
    setUser(null);
    router.push('/');
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
