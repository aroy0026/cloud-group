import { useNavigate } from "react-router";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Image as ImageIcon, Video, Tag, Bell, ArrowRight, TrendingUp } from "lucide-react";
import { SAMPLE_MEDIA } from "./sample-data";
import { MediaCard } from "./MediaCard";

export function Dashboard() {
  const navigate = useNavigate();
  const stats = [
    { label: "Total media", value: "1,284", icon: ImageIcon, hint: "+24 this week" },
    { label: "Videos", value: "97", icon: Video, hint: "+3 this week" },
    { label: "Unique tags", value: "142", icon: Tag, hint: "Auto‑generated" },
    { label: "Subscriptions", value: "5", icon: Bell, hint: "Active alerts" },
  ];
  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm text-muted-foreground">Home</p>
        <h1>Dashboard</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Welcome back. Here's an overview of your wildlife media library.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((s) => (
          <Card key={s.label} className="border-border">
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{s.label}</p>
                  <p className="text-2xl mt-1 text-foreground">{s.value}</p>
                  <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                    <TrendingUp className="h-3 w-3" /> {s.hint}
                  </p>
                </div>
                <div className="h-10 w-10 rounded-lg bg-secondary text-primary flex items-center justify-center">
                  <s.icon className="h-5 w-5" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2 border-border">
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle>Recent uploads</CardTitle>
            <Button variant="ghost" size="sm" onClick={() => navigate("/upload")}>
              Upload more <ArrowRight className="ml-1 h-4 w-4" />
            </Button>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {SAMPLE_MEDIA.slice(0, 6).map((m) => (
                <MediaCard key={m.id} media={m} />
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="border-border">
          <CardHeader>
            <CardTitle>Top species</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {[
              { name: "kangaroo", count: 412 },
              { name: "koala", count: 287 },
              { name: "wombat", count: 134 },
              { name: "dingo", count: 76 },
              { name: "echidna", count: 41 },
            ].map((s) => (
              <div key={s.name}>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="capitalize">{s.name}</span>
                  <Badge variant="secondary">{s.count}</Badge>
                </div>
                <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                  <div className="h-full bg-primary" style={{ width: `${(s.count / 412) * 100}%` }} />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
