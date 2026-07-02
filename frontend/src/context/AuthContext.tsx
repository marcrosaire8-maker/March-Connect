import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { authApi } from "../api";
import {
  clearPrefsConfiguredForEmail,
  clearToken,
  getToken,
  hasPrefsConfiguredForEmail,
  hasPrefsConfiguredInSession,
  markPrefsConfiguredForEmail,
  markPrefsConfiguredInSession,
  setToken,
} from "../api/client";
import type { AppleAuthResponse, GoogleAuthResponse, RegisterResponse, User } from "../api/types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (
    email: string,
    password: string,
    options?: { prenom?: string; nom?: string }
  ) => Promise<RegisterResponse>;
  verifyEmail: (email: string, code: string) => Promise<User>;
  loginWithGoogle: (credential: string) => Promise<GoogleAuthResponse & { user?: User }>;
  completeGoogleLink: (linkToken: string, password: string) => Promise<User>;
  loginWithApple: (
    credential: string,
    options?: { prenom?: string; nom?: string }
  ) => Promise<AppleAuthResponse & { user?: User }>;
  completeAppleLink: (linkToken: string, password: string) => Promise<User>;
  logout: () => void;
  deleteAccount: (password: string) => Promise<void>;
  refreshUser: () => Promise<User | null>;
  markPreferencesConfigured: () => void;
  isAuthenticated: boolean;
  isAdmin: boolean;
  preferencesConfigured: boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async (): Promise<User | null> => {
    const token = getToken();
    if (!token) {
      setUser(null);
      return null;
    }
    try {
      const me = await authApi.me();
      if (me.preferences_configurees) {
        markPrefsConfiguredForEmail(me.email);
      }
      setUser(me);
      return me;
    } catch {
      clearToken();
      setUser(null);
      return null;
    }
  }, []);

  const markPreferencesConfigured = useCallback(() => {
    setUser((prev) => {
      if (prev?.email) {
        markPrefsConfiguredForEmail(prev.email);
      } else {
        markPrefsConfiguredInSession();
      }
      return prev ? { ...prev, preferences_configurees: true } : prev;
    });
  }, []);

  useEffect(() => {
    refreshUser().finally(() => setLoading(false));
  }, [refreshUser]);

  const login = useCallback(async (email: string, password: string) => {
    const normalizedEmail = email.trim().toLowerCase();
    const { access_token } = await authApi.login(normalizedEmail, password);
    setToken(access_token);
    const me = await authApi.me();
    if (me.preferences_configurees) {
      markPrefsConfiguredForEmail(me.email);
    }
    setUser(me);
    return me;
  }, []);

  const register = useCallback(
    async (
      email: string,
      password: string,
      options?: { prenom?: string; nom?: string }
    ): Promise<RegisterResponse> => {
      const normalizedEmail = email.trim().toLowerCase();
      return authApi.register(normalizedEmail, password, options);
    },
    []
  );

  const verifyEmail = useCallback(async (email: string, code: string) => {
    const normalizedEmail = email.trim().toLowerCase();
    const { access_token } = await authApi.verifyEmail(normalizedEmail, code);
    setToken(access_token);
    const me = await authApi.me();
    if (me.preferences_configurees) {
      markPrefsConfiguredForEmail(me.email);
    }
    setUser(me);
    return me;
  }, []);

  const loginWithGoogle = useCallback(async (credential: string) => {
    const result = await authApi.googleAuth(credential);
    if (result.status === "link_required") {
      return result;
    }
    if (!result.access_token) {
      throw new Error("Réponse Google invalide");
    }
    setToken(result.access_token);
    const me = await authApi.me();
    if (me.preferences_configurees) {
      markPrefsConfiguredForEmail(me.email);
    }
    setUser(me);
    return { ...result, user: me };
  }, []);

  const completeGoogleLink = useCallback(async (linkToken: string, password: string) => {
    const { access_token } = await authApi.googleLink(linkToken, password);
    setToken(access_token);
    const me = await authApi.me();
    if (me.preferences_configurees) {
      markPrefsConfiguredForEmail(me.email);
    }
    setUser(me);
    return me;
  }, []);

  const loginWithApple = useCallback(
    async (credential: string, options?: { prenom?: string; nom?: string }) => {
      const result = await authApi.appleAuth(credential, options);
      if (result.status === "link_required") {
        return result;
      }
      if (!result.access_token) {
        throw new Error("Réponse Apple invalide");
      }
      setToken(result.access_token);
      const me = await authApi.me();
      if (me.preferences_configurees) {
        markPrefsConfiguredForEmail(me.email);
      }
      setUser(me);
      return { ...result, user: me };
    },
    []
  );

  const completeAppleLink = useCallback(async (linkToken: string, password: string) => {
    const { access_token } = await authApi.appleLink(linkToken, password);
    setToken(access_token);
    const me = await authApi.me();
    if (me.preferences_configurees) {
      markPrefsConfiguredForEmail(me.email);
    }
    setUser(me);
    return me;
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
  }, []);

  const deleteAccount = useCallback(async (password: string) => {
    const email = user?.email;
    await authApi.deleteAccount(password);
    if (email) {
      clearPrefsConfiguredForEmail(email);
    }
    clearToken();
    setUser(null);
  }, [user?.email]);

  const value = useMemo(
    () => ({
      user,
      loading,
      login,
      register,
      verifyEmail,
      loginWithGoogle,
      completeGoogleLink,
      loginWithApple,
      completeAppleLink,
      logout,
      deleteAccount,
      refreshUser,
      markPreferencesConfigured,
      isAuthenticated: !!user,
      isAdmin: user?.role === "admin",
      preferencesConfigured:
        !!user?.preferences_configurees ||
        hasPrefsConfiguredForEmail(user?.email) ||
        hasPrefsConfiguredInSession(),
    }),
    [user, loading, login, register, verifyEmail, loginWithGoogle, completeGoogleLink, loginWithApple, completeAppleLink, logout, deleteAccount, refreshUser, markPreferencesConfigured]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
