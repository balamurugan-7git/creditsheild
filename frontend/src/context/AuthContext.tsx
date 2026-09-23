// ============================================================
// CrediShield AI – Authentication Context
// Manages JWT storage, user state, and auth operations
// ============================================================

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { loginUser, registerUser, getCurrentUser } from '@/api/auth';
import { getStoredToken, setStoredToken, clearStoredToken } from '@/api/client';
import type { User, UserRole } from '@/types';

// ---- Context shape ---- //
interface AuthContextValue {
  /** The authenticated user, or null if logged out */
  user: User | null;
  /** Convenience accessor for the user's role */
  role: UserRole | null;
  /** True when the user has a valid token and user object */
  isAuthenticated: boolean;
  /** True while the initial token verification is running */
  isLoading: boolean;
  /** Sign in with email + password; throws on failure */
  login: (email: string, password: string) => Promise<void>;
  /** Register a new account; throws on failure */
  register: (
    email: string,
    password: string,
    fullName: string,
    role: UserRole,
  ) => Promise<void>;
  /** Clear session state and token */
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

// ---- Provider ---- //
interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // On mount: if there's a stored token, verify it by fetching /api/auth/me
  useEffect(() => {
    const token = getStoredToken();
    if (!token || token === 'undefined' || token === 'null') {
      clearStoredToken();
      setIsLoading(false);
      return;
    }

    getCurrentUser()
      .then((fetchedUser) => {
        if (!fetchedUser || typeof fetchedUser !== 'object' || !fetchedUser.email) {
          clearStoredToken();
          setUser(null);
        } else {
          setUser(fetchedUser);
        }
      })
      .catch(() => {
        // Token is invalid or expired – clear it
        clearStoredToken();
        setUser(null);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, []);

  const login = useCallback(async (email: string, password: string): Promise<void> => {
    const tokens = await loginUser(email, password);
    if (!tokens || !tokens.access_token) {
      throw new Error('Authentication failed: No access token received from API.');
    }
    setStoredToken(tokens.access_token);
    const fetchedUser = await getCurrentUser();
    if (!fetchedUser || typeof fetchedUser !== 'object' || !fetchedUser.email) {
      throw new Error('Failed to retrieve user profile.');
    }
    setUser(fetchedUser);
  }, []);

  const register = useCallback(
    async (
      email: string,
      password: string,
      fullName: string,
      role: UserRole,
    ): Promise<void> => {
      await registerUser(email, password, fullName, role);
      // Registration does not auto-login; user must sign in manually
    },
    [],
  );

  const logout = useCallback((): void => {
    clearStoredToken();
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      role: user?.role ?? null,
      isAuthenticated: user !== null,
      isLoading,
      login,
      register,
      logout,
    }),
    [user, isLoading, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// ---- Hook ---- //
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used inside <AuthProvider>');
  }
  return ctx;
}
