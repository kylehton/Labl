"use client";
import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { useRouter } from "next/navigation";

interface User {
  id: string;
  email: string;
  name: string;
  picture: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: () => void;
  logout: () => Promise<void>;
  refetch: () => Promise<void>;
}

const SERVER_URL = process.env.NEXT_PUBLIC_SERVER_URL!;

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {

  const router = useRouter();

  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const checkAuthStatus = async () => {
    try {
      const response = await fetch(`${SERVER_URL}/api/user/auth/status`, {
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        if (data.authenticated) {
          setUser(data.user);
        } else {
          console.log("User not authenticated.")
          setUser(null);
        }
      } else {
        console.log("Response Error: No User.")
        setUser(null);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const login = () => {
    // Direct redirect to API endpoint for Google login
    window.location.href = `${SERVER_URL}/api/google/auth/login`;
  };

  const logout = async () => {
    try {
      await fetch(`${SERVER_URL}/api/google/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      });
      setUser(null);
      router.push("/")
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const refetch = async () => {
    setLoading(true);
    await checkAuthStatus();
  };

  const isAuthenticated = !!user;

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, loading, login, logout, refetch }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}

// Custom hook for making authenticated API calls
export function useAuthenticatedFetch() {
  const { refetch } = useAuth();

  const authenticatedFetch = async (url: string, options?: RequestInit) => {
    const response = await fetch(url, {
      ...options,
      credentials: 'include',
    });

    // If unauthorized, try to refetch auth status
    if (response.status === 401) {
      await refetch();
    }
    return response;
  };

  return authenticatedFetch;
}