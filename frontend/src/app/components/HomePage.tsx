import { Link } from "react-router";
import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";
import { Badge } from "./ui/badge";
import { Logo } from "./Logo";
import { ImageWithFallback } from "./figma/ImageWithFallback";
import {
  UploadCloud, Search, Tags, Bell, ShieldCheck, Cloud, Sparkles, ArrowRight, Leaf,
} from "lucide-react";
import { useAuth } from "../auth";

const FEATURES = [
  { icon: UploadCloud, title: "Smart uploads", body: "Drag‑and‑drop images and videos. Checksums catch duplicates before they hit storage." },
  { icon: Sparkles, title: "Auto‑tagging", body: "Each upload is analysed and tagged with detected species and counts — no manual work." },
  { icon: Search, title: "Powerful queries", body: "Search by tag counts, species, thumbnail URL, or even by uploading a sample file." },
  { icon: Tags, title: "Bulk tag editing", body: "Add, remove, or delete tags across many files with safe confirmation flows." },
  { icon: Bell, title: "Tag subscriptions", body: "Get an email when new media matching the species you care about is added." },
  { icon: Cloud, title: "Multi‑cloud serverless", body: "Built on AWS, GCP, and Azure managed services — scalable and cost‑efficient." },
];

export function HomePage() {
  const { email } = useAuth();
  return (
    <div className="min-h-screen bg-background">
      <header className="h-14 border-b border-border bg-card/80 backdrop-blur sticky top-0 z-30">
        <div className="max-w-6xl mx-auto h-full px-4 flex items-center justify-between">
          <Logo />
          <nav className="flex items-center gap-2">
            {email ? (
              <Button asChild>
                <Link to="/dashboard">Open dashboard <ArrowRight className="ml-1.5 h-4 w-4" /></Link>
              </Button>
            ) : (
              <>
                <Button asChild variant="ghost"><Link to="/signin">Sign in</Link></Button>
                <Button asChild><Link to="/signup">Get started</Link></Button>
              </>
            )}
          </nav>
        </div>
      </header>

      <section className="relative overflow-hidden"
        style={{ background: "linear-gradient(180deg, #f1f7ef 0%, #ffffff 70%)" }}>
        <div className="max-w-6xl mx-auto px-4 py-16 md:py-24 grid grid-cols-1 lg:grid-cols-2 gap-10 items-center">
          <div>
            <Badge variant="secondary" className="mb-4">
              <Leaf className="h-3 w-3 mr-1" /> Conservation tech for FIT5225
            </Badge>
            <h1 className="text-3xl md:text-5xl tracking-tight text-foreground leading-tight">
              Catalogue Australian wildlife with{" "}
              <span className="text-primary">auto‑tagged</span> media.
            </h1>
            <p className="mt-4 text-base text-muted-foreground max-w-xl">
              Aussie EcoLens is a multi‑cloud, serverless platform for students and researchers
              to upload wildlife images and videos, run rich queries, and manage tag‑based
              notifications — all from one clean workspace.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              {email ? (
                <Button asChild size="lg">
                  <Link to="/dashboard">Go to dashboard <ArrowRight className="ml-1.5 h-4 w-4" /></Link>
                </Button>
              ) : (
                <>
                  <Button asChild size="lg">
                    <Link to="/signup">Create free account</Link>
                  </Button>
                  <Button asChild size="lg" variant="outline">
                    <Link to="/signin">Sign in</Link>
                  </Button>
                </>
              )}
            </div>
            <p className="mt-4 text-xs text-muted-foreground flex items-center gap-1.5">
              <ShieldCheck className="h-3.5 w-3.5" /> You must sign in to upload media or run queries.
            </p>
          </div>

          <div className="relative">
            <div className="aspect-[4/3] rounded-2xl overflow-hidden border border-border shadow-sm">
              <ImageWithFallback
                src="https://images.unsplash.com/photo-1680924667747-128ea49c4638?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=1200&q=80"
                alt="Koala in eucalyptus tree"
                className="w-full h-full object-cover"
              />
            </div>
            <div className="absolute -bottom-4 -left-4 bg-card border border-border rounded-xl shadow-md p-3 flex items-center gap-3 max-w-[240px]">
              <div className="h-9 w-9 rounded-lg bg-secondary text-primary flex items-center justify-center">
                <Sparkles className="h-4 w-4" />
              </div>
              <div className="text-xs">
                <div className="text-foreground">Auto‑tags detected</div>
                <div className="text-muted-foreground">koala ×3 · tree ×1</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-4 py-14">
        <div className="text-center max-w-2xl mx-auto mb-10">
          <h2>Everything you need to manage a wildlife media library</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            From ingest to discovery — built around the four query types in the FIT5225 brief.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {FEATURES.map((f) => (
            <Card key={f.title} className="border-border">
              <CardContent className="p-5">
                <div className="h-10 w-10 rounded-lg bg-secondary text-primary flex items-center justify-center">
                  <f.icon className="h-5 w-5" />
                </div>
                <h3 className="mt-3">{f.title}</h3>
                <p className="text-sm text-muted-foreground mt-1">{f.body}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="bg-secondary/40 border-y border-border">
        <div className="max-w-6xl mx-auto px-4 py-12 grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
          {[
            { v: "1,200+", l: "Media items catalogued" },
            { v: "140+", l: "Unique species tags" },
            { v: "4", l: "Query types supported" },
            { v: "3", l: "Cloud providers" },
          ].map((s) => (
            <div key={s.l}>
              <div className="text-2xl text-primary">{s.v}</div>
              <div className="text-xs text-muted-foreground mt-1">{s.l}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="max-w-3xl mx-auto px-4 py-16 text-center">
        <h2>Ready to start tagging?</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Sign up in seconds and upload your first wildlife image — tags appear automatically.
        </p>
        <div className="mt-5 flex justify-center gap-3">
          {email ? (
            <Button asChild size="lg"><Link to="/upload">Upload media</Link></Button>
          ) : (
            <Button asChild size="lg"><Link to="/signup">Create free account</Link></Button>
          )}
        </div>
      </section>

      <footer className="border-t border-border py-6 text-center text-xs text-muted-foreground">
        Built as a multi‑cloud serverless app for FIT5225
      </footer>
    </div>
  );
}
