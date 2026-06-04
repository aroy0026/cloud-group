import { useState } from "react";
import "./components/eco-theme.css";
import { Toaster } from "./components/ui/sonner";
import { AuthScreen } from "./components/AuthScreen";
import { AppShell, type View } from "./components/AppShell";
import { Dashboard } from "./components/Dashboard";
import { UploadPage } from "./components/UploadPage";
import { SearchPage } from "./components/SearchPage";
import { TagsPage } from "./components/TagsPage";

export default function App() {
  const [email, setEmail] = useState<string | null>(null);
  const [view, setView] = useState<View>("dashboard");

  return (
    <div className="eco-app size-full min-h-screen">
      {!email ? (
        <AuthScreen onAuthenticated={setEmail} />
      ) : (
        <AppShell
          email={email}
          view={view}
          onChangeView={setView}
          onSignOut={() => setEmail(null)}
        >
          {view === "dashboard" && <Dashboard onNavigate={(v) => setView(v as View)} />}
          {view === "upload" && <UploadPage />}
          {view === "search" && <SearchPage />}
          {view === "tags" && <TagsPage />}
        </AppShell>
      )}
      <Toaster richColors position="bottom-right" />
    </div>
  );
}
