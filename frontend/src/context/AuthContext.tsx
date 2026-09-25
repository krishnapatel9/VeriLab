import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { jwtDecode } from "jwt-decode";
import { apiClient } from "../api/client";

interface User {
  sub: string;
  role: string;
  tenant_id: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (token: string) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(localStorage.getItem("verilab_token"));
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    if (token) {
      try {
        const decoded = jwtDecode<User>(token);
        setUser(decoded);
        apiClient.defaults.headers.common["Authorization"] = `Bearer ${token}`;
      } catch (err) {
        logout();
      }
    } else {
      setUser(null);
      delete apiClient.defaults.headers.common["Authorization"];
    }
  }, [token]);

  const login = (newToken: string) => {
    localStorage.setItem("verilab_token", newToken);
    setToken(newToken);
  };

  const logout = () => {
    localStorage.removeItem("verilab_token");
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
