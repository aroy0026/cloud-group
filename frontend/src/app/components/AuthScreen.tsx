import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Alert, AlertDescription } from "./ui/alert";
import { Loader2, Info, AlertCircle } from "lucide-react";
import { Logo } from "./Logo";
import { useAuth } from "../auth";
import { toast } from "sonner";

type Mode = "signin" | "signup";

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
      if (password.length < 8 || !/[a-zA-Z]/.test(password) || !/\d/.test(password)) {
        setError("Password must be at least 8 characters and contain letters and numbers.");
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
        navigate("/signin", {
          replace: true,
          state: { info: "Please check your email to verify your account." },
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
                <p className="text-xs text-muted-foreground">At least 8 characters, with letters and numbers.</p>
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
