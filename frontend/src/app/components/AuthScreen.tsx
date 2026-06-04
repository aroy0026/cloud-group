import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Alert, AlertDescription } from "./ui/alert";
import { Loader2, Info, AlertCircle, CheckCircle2, Circle } from "lucide-react";
import { Logo } from "./Logo";
import { useAuth } from "../auth";
import { toast } from "sonner";

type Mode = "signin" | "signup";

const PASSWORD_RULES = [
  { id: "length", label: "At least 8 characters", test: (value: string) => value.length >= 8 },
  { id: "letter", label: "Contains a letter", test: (value: string) => /[a-zA-Z]/.test(value) },
  { id: "number", label: "Contains a number", test: (value: string) => /\d/.test(value) },
];

export function AuthScreen({ mode }: { mode: Mode }) {
  const navigate = useNavigate();
  const location = useLocation();
  const { signIn, signUp } = useAuth();
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [first, setFirst] = useState("");
  const [last, setLast] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(
    (location.state as { info?: string } | null)?.info ?? null
  );

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setInfo(null);
    const trimmedEmail = email.trim().toLowerCase();

    if (!isValidEmail(trimmedEmail)) {
      setError("Please enter a valid email address.");
      return;
    }

    if (mode === "signup") {
      if (!first.trim() || !last.trim()) {
        setError("Please enter your first and last name.");
        return;
      }
      if (!passwordMeetsPolicy(password)) {
        setError("Please choose a password that meets every listed policy rule.");
        return;
      }
      if (password !== confirm) {
        setError("Passwords do not match.");
        return;
      }
    }

    if (!password) {
      setError("Please enter your password.");
      return;
    }

    setLoading(true);
    try {
      if (mode === "signup") {
        await signUp({
          firstName: first.trim(),
          lastName: last.trim(),
          email: trimmedEmail,
          password,
        });
        toast.success("Account created", { description: "Please verify your email before signing in." });
        navigate("/verify-email", {
          replace: true,
          state: { email: trimmedEmail },
        });
      } else {
        await signIn({ email: trimmedEmail, password });
        toast.success("Signed in successfully");
        navigate("/dashboard", { replace: true });
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Authentication failed. Please try again.";
      setError(message);
      toast.error(mode === "signin" ? "Sign in failed" : "Sign up failed", { description: message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-center px-4 py-10"
      style={{ background: "linear-gradient(180deg, #f1f7ef 0%, #ffffff 60%)" }}>
      <div className="w-full max-w-md">
        <div className="flex flex-col items-center text-center mb-6">
          <Logo size="lg" />
          <p className="mt-3 text-sm text-muted-foreground">Multi‑cloud wildlife media tagging platform</p>
        </div>

        <div className="bg-card border border-border rounded-xl shadow-sm p-6">
          <div className="mb-5">
            <h1 className="text-foreground">{mode === "signin" ? "Sign in" : "Create your account"}</h1>
            <p className="text-sm text-muted-foreground mt-1">
              {mode === "signin"
                ? "Welcome back. Sign in to continue."
                : "Start uploading and tagging wildlife media."}
            </p>
          </div>

          {info && (
            <Alert className="mb-4 border-primary/30 bg-secondary">
              <Info className="h-4 w-4" />
              <AlertDescription>{info}</AlertDescription>
            </Alert>
          )}
          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <form onSubmit={submit} className="space-y-4">
            {mode === "signup" && (
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label htmlFor="first">First name</Label>
                  <Input id="first" placeholder="Jane" value={first} onChange={(e) => setFirst(e.target.value)} disabled={loading} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="last">Last name</Label>
                  <Input id="last" placeholder="Doe" value={last} onChange={(e) => setLast(e.target.value)} disabled={loading} />
                </div>
              </div>
            )}

            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" placeholder="you@university.edu"
                value={email} onChange={(e) => setEmail(e.target.value)} disabled={loading} />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <Input id="password" type="password" placeholder="••••••••"
                value={password} onChange={(e) => setPassword(e.target.value)} disabled={loading} />
              {mode === "signup" && (
                <PasswordPolicyChecklist password={password} confirm={confirm} />
              )}
            </div>

            {mode === "signup" && (
              <div className="space-y-1.5">
                <Label htmlFor="confirm">Confirm password</Label>
                <Input id="confirm" type="password" placeholder="••••••••"
                  value={confirm} onChange={(e) => setConfirm(e.target.value)} disabled={loading} />
              </div>
            )}

            <Button type="submit" className="w-full" disabled={loading}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {mode === "signin" ? "Sign in" : "Sign up"}
            </Button>
          </form>

          <div className="mt-5 text-center text-sm">
            {mode === "signin" ? (
              <>
                Don't have an account?{" "}
                <Link to="/signup" className="text-primary hover:underline">Create one</Link>
                <span className="mx-2 text-muted-foreground">·</span>
                <Link to="/verify-email" className="text-primary hover:underline">Verify email</Link>
              </>
            ) : (
              <>
                Already have an account?{" "}
                <Link to="/signin" className="text-primary hover:underline">Sign in</Link>
              </>
            )}
          </div>

          <p className="mt-5 text-xs text-muted-foreground text-center border-t border-border pt-4">
            You must sign in to upload media or run queries.
          </p>
        </div>

        <p className="mt-6 text-xs text-muted-foreground text-center">
          Built as a multi‑cloud serverless app for FIT5225
        </p>
      </div>
    </div>
  );
}

function isValidEmail(value: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

function passwordMeetsPolicy(password: string) {
  return PASSWORD_RULES.every((rule) => rule.test(password));
}

function PasswordPolicyChecklist({ password, confirm }: { password: string; confirm: string }) {
  const matchReady = confirm.length > 0;
  const passwordsMatch = matchReady && password === confirm;

  return (
    <div className="rounded-lg border border-border bg-accent/30 p-3 space-y-2">
      <p className="text-xs text-muted-foreground">Password policy</p>
      <div className="space-y-1.5">
        {PASSWORD_RULES.map((rule) => (
          <PasswordRule key={rule.id} valid={rule.test(password)} label={rule.label} />
        ))}
        <PasswordRule
          valid={passwordsMatch}
          neutral={!matchReady}
          label={matchReady ? "Passwords match" : "Confirm password to verify match"}
        />
      </div>
    </div>
  );
}

function PasswordRule({ valid, neutral = false, label }: { valid: boolean; neutral?: boolean; label: string }) {
  const Icon = valid ? CheckCircle2 : Circle;
  return (
    <div className={`flex items-center gap-2 text-xs ${valid ? "text-primary" : neutral ? "text-muted-foreground" : "text-destructive"}`}>
      <Icon className="h-3.5 w-3.5" />
      <span>{label}</span>
    </div>
  );
}
