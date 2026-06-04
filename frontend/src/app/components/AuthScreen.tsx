import { useState } from "react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Alert, AlertDescription } from "./ui/alert";
import { Loader2, Info, AlertCircle } from "lucide-react";
import { Logo } from "./Logo";

type Mode = "signin" | "signup";

export function AuthScreen({ onAuthenticated }: { onAuthenticated: (email: string) => void }) {
  const [mode, setMode] = useState<Mode>("signin");
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [first, setFirst] = useState("");
  const [last, setLast] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setInfo(null);
    if (mode === "signup") {
      if (password.length < 8 || !/[a-zA-Z]/.test(password) || !/\d/.test(password)) {
        setError("Password must be at least 8 characters and contain letters and numbers.");
        return;
      }
      if (password !== confirm) {
        setError("Passwords do not match.");
        return;
      }
    }
    if (!email) {
      setError("Please enter a valid email.");
      return;
    }
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      if (mode === "signup") {
        setInfo("Please check your email to verify your account.");
        setMode("signin");
      } else {
        onAuthenticated(email);
      }
    }, 900);
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
                  <Input id="first" placeholder="Jane" value={first} onChange={(e) => setFirst(e.target.value)} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="last">Last name</Label>
                  <Input id="last" placeholder="Doe" value={last} onChange={(e) => setLast(e.target.value)} />
                </div>
              </div>
            )}

            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" placeholder="you@university.edu"
                value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <Input id="password" type="password" placeholder="••••••••"
                value={password} onChange={(e) => setPassword(e.target.value)} />
              {mode === "signup" && (
                <p className="text-xs text-muted-foreground">At least 8 characters, with letters and numbers.</p>
              )}
            </div>

            {mode === "signup" && (
              <div className="space-y-1.5">
                <Label htmlFor="confirm">Confirm password</Label>
                <Input id="confirm" type="password" placeholder="••••••••"
                  value={confirm} onChange={(e) => setConfirm(e.target.value)} />
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
                <button className="text-primary hover:underline" onClick={() => { setMode("signup"); setError(null); setInfo(null); }}>
                  Create one
                </button>
              </>
            ) : (
              <>
                Already have an account?{" "}
                <button className="text-primary hover:underline" onClick={() => { setMode("signin"); setError(null); setInfo(null); }}>
                  Sign in
                </button>
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
