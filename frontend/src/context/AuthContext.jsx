import { createContext, useCallback, useContext, useEffect, useState } from "react";
import {
  fetchMe,
  loginUser,
  logoutUser,
  registerUser,
} from "../services/authService.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [business, setBusiness] = useState(null);
  const [onboardingCompleted, setOnboardingCompleted] = useState(false);
  const [loading, setLoading] = useState(true);

  const refreshAuth = useCallback(async () => {
    try {
      const data = await fetchMe();
      setUser(data.user || null);
      setBusiness(data.business || null);
      setOnboardingCompleted(Boolean(data.onboarding_completed));
      return data;
    } catch {
      setUser(null);
      setBusiness(null);
      setOnboardingCompleted(false);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshAuth();
  }, [refreshAuth]);

  const login = useCallback(async (payload) => {
    try {
      localStorage.removeItem("chitragupta_active_ai_conversation");
    } catch {
      // ignore
    }
    const data = await loginUser(payload);
    setUser(data.user || null);
    setBusiness(data.business || null);
    setOnboardingCompleted(Boolean(data.onboarding_completed));
    return data;
  }, []);

  const register = useCallback(async (payload) => {
    try {
      localStorage.removeItem("chitragupta_active_ai_conversation");
    } catch {
      // ignore
    }
    const data = await registerUser(payload);
    setUser(data.user || null);
    setBusiness(data.business || null);
    setOnboardingCompleted(Boolean(data.onboarding_completed));
    return data;
  }, []);

  const logout = useCallback(async () => {
    try {
      localStorage.removeItem("chitragupta_active_ai_conversation");
      await logoutUser();
    } finally {
      setUser(null);
      setBusiness(null);
      setOnboardingCompleted(false);
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        business,
        onboardingCompleted,
        loading,
        isAuthenticated: Boolean(user),
        login,
        register,
        logout,
        refreshAuth,
        setBusiness,
        setOnboardingCompleted,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return ctx;
}
