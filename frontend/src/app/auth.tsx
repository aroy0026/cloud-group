import { createContext, useContext, useState, type ReactNode } from "react";
import { Navigate, useLocation } from "react-router";
import { api } from "./api";

type AuthCtx = {
  email: string | null;
  token: string | null;
  signIn: (input: { email: string; password: string }) => Promise<void>;
  signUp: (input: { firstName: string; lastName: string; email: string; password: string }) => Promise<void>;
  signOut: () => Promise<void>;
};

const Ctx = createContext<AuthCtx | null>(null);
const EMAIL_KEY = "ecolens_email";
const TOKEN_KEY = "ecolens_token";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [email, setEmail] = useState<string | null>(() => {
    try { return localStorage.getItem(EMAIL_KEY); } catch { return null; }
  });
  const [token, setToken] = useState<string | null>(() => {
    try { return localStorage.getItem(TOKEN_KEY); } catch { return null; }
  });

  const persistSession = (nextEmail: string, nextToken: string) => {
    setEmail(nextEmail);
    setToken(nextToken);
    try {
      localStorage.setItem(EMAIL_KEY, nextEmail);
      localStorage.setItem(TOKEN_KEY, nextToken);
    } catch {}
  };

  const signIn = async (input: { email: string; password: string }) => {
    if (api.enabled) {
      const session = await api.signIn(input);
      persistSession(session.email, session.token);
      return;
    }

    persistSession(input.email, "local-demo-token");
  };

  const signUp = async (input: { firstName: string; lastName: string; email: string; password: string }) => {
    if (api.enabled) await api.signUp(input);
  };

  const signOut = async () => {
    await api.signOut(token);
    setEmail(null);
    setToken(null);
    try {
      localStorage.removeItem(EMAIL_KEY);
      localStorage.removeItem(TOKEN_KEY);
    } catch {}
  };
  return <Ctx.Provider value={{ email, token, signIn, signUp, signOut }}>{children}</Ctx.Provider>;
}

export function useAuth() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth must be used within AuthProvider");
  return v;
}

export function RequireAuth({ children }: { children: ReactNode }) {
  const { email, token } = useAuth();
  const loc = useLocation();
  if (!email || !token) return <Navigate to="/signin" replace state={{ from: loc.pathname }} />;
  return <>{children}</>;
}

export function RedirectIfAuthed({ children }: { children: ReactNode }) {
  const { email } = useAuth();
  if (email) return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}
