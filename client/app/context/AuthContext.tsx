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

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const SERVER_URL = process.env.NEXT_PUBLIC_SERVER_URL || "DNE";

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // 🔑 Fetch auth status from backend
  const checkAuthStatus = async () => {
    try {
      const res = await fetch(`${SERVER_URL}/api/user/auth/status`, {
        credentials: "include", // MUST INCLUDE
      });

      if (res.ok) {
        const data = await res.json();
        if (data.authenticated) {
          setUser(data.user);
        } else {
          setUser(null);
        }
      } else {
        setUser(null);
      }
    } catch (err) {
      console.error("Auth status check failed:", err);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkAuthStatus();
  }, []);

  // 🌐 Redirect user to backend login endpoint
  const login = () => {
    window.location.href = `${SERVER_URL}/api/user/auth/login`;
  };

  const logout = async () => {
    try {
      const res = await fetch(`${SERVER_URL}/api/user/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
      if (res.ok) {
        setUser(null);
        router.push("/"); // landing page
      }
    } catch (err) {
      console.error("Logout failed:", err);
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

// Hook to access AuthContext
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}

// Custom hook for authenticated fetch requests
export function useAuthenticatedFetch() {
  const { refetch } = useAuth();

  const authenticatedFetch = async (url: string, options?: RequestInit) => {
    const res = await fetch(url, {
      ...options,
      credentials: "include",
    });

    // If session expired, try to refresh
    if (res.status === 401) {
      await refetch();
    }
    return res;
  };

  return authenticatedFetch;
}
