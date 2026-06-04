import { useState } from "react";
import { Logo } from "./Logo";
import { Button } from "./ui/button";
import { Avatar, AvatarFallback } from "./ui/avatar";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { LayoutDashboard, UploadCloud, Search, Tags, LogOut, User, Menu, X } from "lucide-react";

export type View = "dashboard" | "upload" | "search" | "tags";

const NAV: { id: View; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "upload", label: "Upload media", icon: UploadCloud },
  { id: "search", label: "Search media", icon: Search },
  { id: "tags", label: "Tags & notifications", icon: Tags },
];

export function AppShell({
  email,
  view,
  onChangeView,
  onSignOut,
  children,
}: {
  email: string;
  view: View;
  onChangeView: (v: View) => void;
  onSignOut: () => void;
  children: React.ReactNode;
}) {
  const [mobileOpen, setMobileOpen] = useState(false);
  return (
    <div className="min-h-screen flex flex-col bg-background">
      <header className="h-14 border-b border-border bg-card flex items-center justify-between px-4 sticky top-0 z-30">
        <div className="flex items-center gap-3">
          <button className="md:hidden" onClick={() => setMobileOpen((v) => !v)}>
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
          <Logo />
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-9 gap-2 px-2">
              <Avatar className="h-7 w-7">
                <AvatarFallback className="bg-primary text-primary-foreground text-xs">
                  {email.slice(0, 2).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <span className="hidden sm:inline text-sm">{email}</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuLabel>{email}</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem><User className="mr-2 h-4 w-4" /> Profile</DropdownMenuItem>
            <DropdownMenuItem onClick={onSignOut}><LogOut className="mr-2 h-4 w-4" /> Sign out</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </header>

      <div className="flex-1 flex">
        <aside
          className={`${mobileOpen ? "block" : "hidden"} md:block w-60 shrink-0 border-r border-sidebar-border bg-sidebar text-sidebar-foreground sticky top-14 self-start h-[calc(100vh-3.5rem)]`}
        >
          <nav className="p-3 space-y-1">
            {NAV.map((n) => {
              const active = view === n.id;
              return (
                <button
                  key={n.id}
                  onClick={() => { onChangeView(n.id); setMobileOpen(false); }}
                  className={`w-full flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                    active
                      ? "bg-sidebar-primary text-sidebar-primary-foreground"
                      : "hover:bg-sidebar-accent text-sidebar-foreground"
                  }`}
                >
                  <n.icon className="h-4 w-4" />
                  {n.label}
                </button>
              );
            })}
          </nav>
          <div className="mt-auto px-4 py-3 text-xs text-muted-foreground">
            Multi‑cloud serverless · FIT5225
          </div>
        </aside>

        <main className="flex-1 min-w-0">
          <div className="max-w-[1440px] mx-auto p-6">{children}</div>
          <footer className="border-t border-border py-4 text-center text-xs text-muted-foreground">
            Built as a multi‑cloud serverless app for FIT5225
          </footer>
        </main>
      </div>
    </div>
  );
}
