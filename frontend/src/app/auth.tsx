import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { Navigate, useLocation } from "react-router";
import { api } from "./api";
import {
  cognitoConfirmSignUp,
  cognitoEnabled,
  cognitoGetCurrentSession,
  cognitoResendConfirmationCode,
  cognitoSignIn,
  cognitoSignOut,
  cognitoSignUp,
} from "./cognito";

type AuthCtx = {
  email: string | null;
  token: string | null;
  checkingSession: boolean;
  signIn: (input: { email: string; password: string }) => Promise<void>;
  signUp: (input: { firstName: string; lastName: string; email: string; password: string }) => Promise<void>;
  confirmSignUp: (input: { email: string; code: string }) => Promise<void>;
  resendConfirmationCode: (email: string) => Promise<void>;
  signOut: () => Promise<void>;
};

const Ctx = createContext<AuthCtx | null>(null);
const EMAIL_KEY = "ecolens_email";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [email, setEmail] = useState<string | null>(() => {
    try { return localStorage.getItem(EMAIL_KEY); } catch { return null; }
  });
  const [token, setToken] = useState<string | null>(null);
  const [checkingSession, setCheckingSession] = useState(cognitoEnabled);

  useEffect(() => {
    if (!cognitoEnabled) {
      setCheckingSession(false);
      return;
    }

    cognitoGetCurrentSession()
      .then((session) => {
        if (session) {
          persistSession(session.email, session.accessToken);
          return;
        }

        setEmail(null);
        setToken(null);
        try {
          localStorage.removeItem(EMAIL_KEY);
        } catch {}
      })
      .finally(() => setCheckingSession(false));
  }, []);

  const persistSession = (nextEmail: string, nextToken: string) => {
    setEmail(nextEmail);
    setToken(nextToken);
    try {
      localStorage.setItem(EMAIL_KEY, nextEmail);
    } catch {}
  };

  const signIn = async (input: { email: string; password: string }) => {
    if (cognitoEnabled) {
      const session = await cognitoSignIn(input);
      persistSession(session.email, session.accessToken);
      return;
    }

    if (api.enabled) {
      const session = await api.signIn(input);
      persistSession(session.email, session.token);
      return;
    }

    persistSession(input.email, "local-demo-token");
  };

  const signUp = async (input: { firstName: string; lastName: string; email: string; password: string }) => {
    if (cognitoEnabled) {
      await cognitoSignUp(input);
      return;
    }

    if (api.enabled) await api.signUp(input);
  };

  const confirmSignUp = async (input: { email: string; code: string }) => {
    if (cognitoEnabled) {
      await cognitoConfirmSignUp(input);
      return;
    }
  };

  const resendConfirmationCode = async (email: string) => {
    if (cognitoEnabled) {
      await cognitoResendConfirmationCode(email);
      return;
    }
  };

  const signOut = async () => {
    if (cognitoEnabled) cognitoSignOut();
    else await api.signOut(token);
    setEmail(null);
    setToken(null);
    try {
      localStorage.removeItem(EMAIL_KEY);
    } catch {}
  };
  return (
    <Ctx.Provider
      value={{
        email,
        token,
        checkingSession,
        signIn,
        signUp,
        confirmSignUp,
        resendConfirmationCode,
        signOut,
      }}
    >
      {children}
    </Ctx.Provider>
  );
}

export function useAuth() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth must be used within AuthProvider");
  return v;
}

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { email, token, checkingSession } = useAuth();
  const loc = useLocation();
  if (checkingSession) return <FullPageLoading />;
  if (!email || !token) return <Navigate to="/signin" replace state={{ from: loc.pathname }} />;
  return <>{children}</>;
}

export const RequireAuth = ProtectedRoute;

export function RedirectIfAuthed({ children }: { children: ReactNode }) {
  const { email, token, checkingSession } = useAuth();
  if (checkingSession) return <FullPageLoading />;
  if (email && token) return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}

function FullPageLoading() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background text-sm text-muted-foreground">
      Loading session...
    </div>
  );
}
