import { createContext, useContext, useState, type ReactNode } from "react";
import { Navigate, useLocation } from "react-router";

type AuthCtx = {
  email: string | null;
  signIn: (email: string) => void;
  signOut: () => void;
};

const Ctx = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [email, setEmail] = useState<string | null>(() => {
    try { return localStorage.getItem("ecolens_email"); } catch { return null; }
  });
  const signIn = (e: string) => {
    setEmail(e);
    try { localStorage.setItem("ecolens_email", e); } catch {}
  };
  const signOut = () => {
    setEmail(null);
    try { localStorage.removeItem("ecolens_email"); } catch {}
  };
  return <Ctx.Provider value={{ email, signIn, signOut }}>{children}</Ctx.Provider>;
}

export function useAuth() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth must be used within AuthProvider");
  return v;
}

export function RequireAuth({ children }: { children: ReactNode }) {
  const { email } = useAuth();
  const loc = useLocation();
  if (!email) return <Navigate to="/signin" replace state={{ from: loc.pathname }} />;
  return <>{children}</>;
}

export function RedirectIfAuthed({ children }: { children: ReactNode }) {
  const { email } = useAuth();
  if (email) return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}
