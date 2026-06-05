import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router";
import { toast } from "sonner";
import { AlertCircle, CheckCircle2, Info, Loader2, MailCheck } from "lucide-react";
import { useAuth } from "../auth";
import { Logo } from "./Logo";
import { Alert, AlertDescription } from "./ui/alert";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";

export function VerifyEmailScreen() {
  const navigate = useNavigate();
  const location = useLocation();
  const { confirmSignUp, resendConfirmationCode } = useAuth();
  const state = location.state as { email?: string } | null;
  const [email, setEmail] = useState(state?.email ?? "");
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const trimmedEmail = email.trim().toLowerCase();
    const trimmedCode = code.trim();

    if (!isValidEmail(trimmedEmail)) {
      setError("Please enter the email address you used to sign up.");
      return;
    }
    if (!trimmedCode) {
      setError("Please enter the verification code from your email.");
      return;
    }

    setLoading(true);
    try {
      await confirmSignUp({ email: trimmedEmail, code: trimmedCode });
      toast.success("Email verified", { description: "You can now sign in." });
      navigate("/signin", {
        replace: true,
        state: { info: "Your email is verified. Please sign in." },
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Could not verify this email.";
      setError(message);
      toast.error("Verification failed", { description: message });
    } finally {
      setLoading(false);
    }
  };

  const resend = async () => {
    setError(null);
    const trimmedEmail = email.trim().toLowerCase();
    if (!isValidEmail(trimmedEmail)) {
      setError("Enter your email address first, then resend the code.");
      return;
    }

    setResending(true);
    try {
      await resendConfirmationCode(trimmedEmail);
      toast.success("Verification code sent", { description: "Check your email for the new code." });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Could not resend the verification code.";
      setError(message);
      toast.error("Resend failed", { description: message });
    } finally {
      setResending(false);
    }
  };

  return (
    <div
      className="min-h-screen w-full flex flex-col items-center justify-center px-4 py-10"
      style={{ background: "linear-gradient(180deg, #f1f7ef 0%, #ffffff 60%)" }}
    >
      <div className="w-full max-w-md">
        <div className="flex flex-col items-center text-center mb-6">
          <Logo size="lg" />
          <p className="mt-3 text-sm text-muted-foreground">Verify your EcoLens account</p>
        </div>

        <div className="bg-card border border-border rounded-xl shadow-sm p-6">
          <div className="mb-5">
            <div className="h-11 w-11 rounded-full bg-secondary text-primary flex items-center justify-center mb-3">
              <MailCheck className="h-5 w-5" />
            </div>
            <h1 className="text-foreground">Verify email</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Enter the code Cognito sent to your email address.
            </p>
          </div>

          <Alert className="mb-4 border-primary/30 bg-secondary">
            <Info className="h-4 w-4" />
            <AlertDescription>
              New users must verify their email before they can sign in.
            </AlertDescription>
          </Alert>

          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <form onSubmit={submit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="verify-email">Email</Label>
              <Input
                id="verify-email"
                type="email"
                placeholder="you@university.edu"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loading}
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="verify-code">Verification code</Label>
              <Input
                id="verify-code"
                inputMode="numeric"
                placeholder="123456"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                disabled={loading}
              />
            </div>

            <Button type="submit" className="w-full" disabled={loading || resending}>
              {loading ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <CheckCircle2 className="mr-2 h-4 w-4" />
              )}
              Verify email
            </Button>
          </form>

          <div className="mt-4 flex flex-col gap-3 text-center text-sm">
            <Button variant="outline" onClick={resend} disabled={loading || resending}>
              {resending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Resend code
            </Button>
            <Link to="/signin" className="text-primary hover:underline">
              Back to sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

function isValidEmail(value: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}
