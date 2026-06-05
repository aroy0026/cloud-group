import { useRef, useState } from "react";
import { useNavigate, useParams } from "react-router";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Card, CardContent } from "./ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Plus, X, Search, UploadCloud, Loader2, ImageOff, ExternalLink } from "lucide-react";
import { toast } from "sonner";
import { MediaCard } from "./MediaCard";
import { MediaPreviewDialog } from "./MediaPreviewDialog";
import { useMediaLibrary, type MediaItem } from "../media-library";

type TagRow = { id: string; tag: string; count: string };

export function SearchPage() {
  const { searchByTags, searchBySpecies, searchByThumbnail, searchByFile } = useMediaLibrary();
  const [tagRows, setTagRows] = useState<TagRow[]>([
    { id: "r1", tag: "", count: "" },
  ]);
  const [species, setSpecies] = useState("");
  const [thumbUrl, setThumbUrl] = useState("");
  const [queryFile, setQueryFile] = useState<File | null>(null);
  const [results, setResults] = useState<MediaItem[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [progressMsg, setProgressMsg] = useState<string | null>(null);
  const [open, setOpen] = useState<MediaItem | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const { tab: tabParam } = useParams();
  const validTabs = ["tags", "species", "thumb", "file"] as const;
  const tab = (validTabs as readonly string[]).includes(tabParam ?? "")
    ? (tabParam as string)
    : "tags";
  const setTab = (v: string) => navigate(`/search/${v}`);

  const runSearch = (searcher: () => MediaItem[] | Promise<MediaItem[]>, msg?: string) => {
    setLoading(true);
    setProgressMsg(msg ?? null);
    Promise.resolve(searcher())
      .then((matches) => {
        setResults(matches);
        if (!matches.length) toast.info("No matching media found.");
      })
      .catch(() => {
        setResults([]);
        toast.error("Search failed", { description: "Please check the query and try again." });
      })
      .finally(() => {
        setLoading(false);
        setProgressMsg(null);
      });
  };

  const updateRow = (id: string, key: "tag" | "count", v: string) =>
    setTagRows((rs) => rs.map((r) => (r.id === id ? { ...r, [key]: v } : r)));

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm text-muted-foreground">Search / {labelFor(tab)}</p>
        <h1>Search media</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Run complex queries across your wildlife library.
        </p>
      </div>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="grid grid-cols-2 md:grid-cols-4 w-full max-w-3xl">
          <TabsTrigger value="tags">By tags & counts</TabsTrigger>
          <TabsTrigger value="species">By species</TabsTrigger>
          <TabsTrigger value="thumb">By thumbnail URL</TabsTrigger>
          <TabsTrigger value="file">By file</TabsTrigger>
        </TabsList>

        <TabsContent value="tags">
          <Card className="border-border">
            <CardContent className="p-5 space-y-4">
              <p className="text-sm text-muted-foreground">
                Search for media that contains all of the specified tags with minimum counts (logical AND).
              </p>
              <div className="space-y-2">
                {tagRows.map((r, idx) => (
                  <div key={r.id} className="flex items-end gap-2">
                    <div className="flex-1 space-y-1.5">
                      <Label>Tag name</Label>
                      <Input
                        placeholder={idx === 0 ? "koala" : idx === 1 ? "wombat" : "tag"}
                        value={r.tag}
                        onChange={(e) => updateRow(r.id, "tag", e.target.value)}
                        disabled={loading}
                      />
                    </div>
                    <div className="w-32 space-y-1.5">
                      <Label>Min count</Label>
                      <Input
                        type="number"
                        min={1}
                        placeholder={idx === 0 ? "3" : "2"}
                        value={r.count}
                        onChange={(e) => updateRow(r.id, "count", e.target.value)}
                        disabled={loading}
                      />
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => setTagRows((rs) => rs.filter((x) => x.id !== r.id))}
                      disabled={tagRows.length === 1 || loading}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  disabled={loading}
                  onClick={() =>
                    setTagRows((rs) => [...rs, { id: `r${Date.now()}`, tag: "", count: "" }])
                  }
                >
                  <Plus className="mr-2 h-4 w-4" /> Add tag
                </Button>
                <Button disabled={loading} onClick={() => {
                  const invalid = tagRows.some((r) => !r.tag.trim() || !Number.isFinite(Number(r.count)) || Number(r.count) < 1);
                  if (invalid) {
                    toast.error("Please enter a tag and a min count greater than zero for each row.");
                    return;
                  }
                  runSearch(() =>
                    searchByTags(tagRows.map((r) => ({ tag: r.tag, minCount: Number(r.count) })))
                  );
                }}>
                  <Search className="mr-2 h-4 w-4" /> Run search
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="species">
          <Card className="border-border">
            <CardContent className="p-5 space-y-4 max-w-xl">
              <div className="space-y-1.5">
                <Label>Species</Label>
                <Input placeholder="dingo" value={species} onChange={(e) => setSpecies(e.target.value)} disabled={loading} />
              </div>
              <Button disabled={loading} onClick={() => {
                if (!species.trim()) {
                  toast.error("Please enter a species name.");
                  return;
                }
                runSearch(() => searchBySpecies(species));
              }}>
                <Search className="mr-2 h-4 w-4" /> Run search
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="thumb">
          <Card className="border-border">
            <CardContent className="p-5 space-y-4 max-w-2xl">
              <div className="space-y-1.5">
                <Label>Thumbnail URL</Label>
                <Input
                  placeholder="https://storage.googleapis.com/.../thumbnails/image123.png"
                  value={thumbUrl}
                  onChange={(e) => setThumbUrl(e.target.value)}
                  disabled={loading}
                />
              </div>
              <Button disabled={loading} onClick={() => {
                if (!thumbUrl.trim()) {
                  toast.error("Please enter a thumbnail URL.");
                  return;
                }
                try {
                  new URL(thumbUrl);
                } catch {
                  toast.error("Please enter a valid thumbnail URL.");
                  return;
                }
                runSearch(() => searchByThumbnail(thumbUrl));
              }}>
                <ExternalLink className="mr-2 h-4 w-4" /> Find original image
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="file">
          <Card className="border-border">
            <CardContent className="p-5 space-y-4 max-w-2xl">
              <div className="border-2 border-dashed border-border rounded-xl p-8 text-center bg-accent/40">
                <div className="h-12 w-12 mx-auto rounded-full bg-secondary text-primary flex items-center justify-center">
                  <UploadCloud className="h-6 w-6" />
                </div>
                <p className="mt-3 text-sm">Upload a file for query only</p>
                <p className="text-xs text-muted-foreground mt-1">
                  The file is analysed for tags but not stored permanently.
                </p>
                <Button className="mt-4" variant="outline" disabled={loading} onClick={() => fileInputRef.current?.click()}>
                  Choose file
                </Button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*,video/*"
                  className="hidden"
                  onChange={(e) => {
                    const file = e.target.files?.[0] ?? null;
                    if (file && !(file.type.startsWith("image/") || file.type.startsWith("video/"))) {
                      toast.error("Please choose an image or video file.");
                      return;
                    }
                    setQueryFile(file);
                  }}
                  onClick={(e) => {
                    e.currentTarget.value = "";
                  }}
                />
                {queryFile && (
                  <p className="text-xs text-muted-foreground mt-3">
                    Selected: {queryFile.name}
                  </p>
                )}
              </div>
              <Button
                disabled={loading}
                onClick={() => {
                  if (!queryFile) {
                    toast.error("Please choose a query file first.");
                    return;
                  }
                  runSearch(() => searchByFile(queryFile), "Analyzing temporary file...");
                  setTimeout(() => setProgressMsg("Searching for matching media..."), 350);
                }}
              >
                <Search className="mr-2 h-4 w-4" /> Run search
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <div>
        <div className="flex items-center justify-between mb-3">
          <h2>Results</h2>
          {results && <span className="text-sm text-muted-foreground">{results.length} match{results.length === 1 ? "" : "es"}</span>}
        </div>

        {loading && (
          <Card className="border-border">
            <CardContent className="p-10 flex flex-col items-center text-center">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <p className="mt-3 text-sm">{progressMsg ?? "Running query…"}</p>
            </CardContent>
          </Card>
        )}

        {!loading && !results && (
          <Card className="border-border">
            <CardContent className="p-10 flex flex-col items-center text-center">
              <div className="h-14 w-14 rounded-full bg-secondary text-primary flex items-center justify-center">
                <ImageOff className="h-7 w-7" />
              </div>
              <h3 className="mt-3">No results yet</h3>
              <p className="text-sm text-muted-foreground mt-1">Try adjusting your search criteria.</p>
            </CardContent>
          </Card>
        )}

        {!loading && results && (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {results.map((m) => (
              <MediaCard key={m.id} media={m} showCheckbox onOpen={setOpen} />
            ))}
          </div>
        )}
      </div>

      <MediaPreviewDialog media={open} onClose={() => setOpen(null)} />
    </div>
  );
}

function labelFor(t: string) {
  return t === "tags" ? "Tags & counts"
    : t === "species" ? "Species"
    : t === "thumb" ? "Thumbnail URL"
    : "File";
}
