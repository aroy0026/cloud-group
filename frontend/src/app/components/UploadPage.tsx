import { useState, useRef } from "react";
import { toast } from "sonner";
import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";
import { Badge } from "./ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./ui/table";
import { UploadCloud, FileVideo, FileImage, AlertTriangle, Loader2, CheckCircle2 } from "lucide-react";
import { SAMPLE_MEDIA } from "./sample-data";
import { MediaCard } from "./MediaCard";

type UploadStatus =
  | "ready"
  | "checksum"
  | "duplicate"
  | "uploading"
  | "processing"
  | "done"
  | "error";

type UploadFile = {
  id: string;
  name: string;
  type: string;
  size: number;
  status: UploadStatus;
};

const STATUS_LABEL: Record<UploadStatus, string> = {
  ready: "Ready to upload",
  checksum: "Calculating checksum…",
  duplicate: "Duplicate – already in library",
  uploading: "Uploading…",
  processing: "Uploaded, processing tags & thumbnails…",
  done: "Complete",
  error: "Upload failed",
};

function statusBadge(s: UploadStatus) {
  const variants: Record<UploadStatus, string> = {
    ready: "bg-secondary text-secondary-foreground",
    checksum: "bg-blue-50 text-blue-700 border border-blue-200",
    duplicate: "bg-amber-50 text-amber-800 border border-amber-200",
    uploading: "bg-blue-50 text-blue-700 border border-blue-200",
    processing: "bg-violet-50 text-violet-700 border border-violet-200",
    done: "bg-emerald-50 text-emerald-700 border border-emerald-200",
    error: "bg-red-50 text-red-700 border border-red-200",
  };
  return (
    <span className={`inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full ${variants[s]}`}>
      {(s === "uploading" || s === "processing" || s === "checksum") && <Loader2 className="h-3 w-3 animate-spin" />}
      {s === "duplicate" && <AlertTriangle className="h-3 w-3" />}
      {s === "done" && <CheckCircle2 className="h-3 w-3" />}
      {STATUS_LABEL[s]}
    </span>
  );
}

function formatSize(b: number) {
  if (b < 1024) return `${b} B`;
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / (1024 * 1024)).toFixed(1)} MB`;
}

export function UploadPage() {
  const [files, setFiles] = useState<UploadFile[]>([
    { id: "f1", name: "koala_riverbank.jpg", type: "image/jpeg", size: 2_400_000, status: "ready" },
  ]);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const addFiles = (list: FileList | File[]) => {
    const arr = Array.from(list);
    const next: UploadFile[] = arr.map((f, i) => ({
      id: `f-${Date.now()}-${i}`,
      name: f.name,
      type: f.type || "application/octet-stream",
      size: f.size,
      status: "checksum",
    }));
    setFiles((prev) => [...next, ...prev]);
    next.forEach((nf, idx) => simulate(nf.id, idx === 0 && nf.name.toLowerCase().includes("dup")));
  };

  const simulate = (id: string, dup = false) => {
    const update = (status: UploadStatus) =>
      setFiles((prev) => prev.map((f) => (f.id === id ? { ...f, status } : f)));
    setTimeout(() => {
      if (dup) {
        update("duplicate");
        toast.warning("Duplicate file detected", { description: "This file already exists in your library." });
        return;
      }
      update("uploading");
      setTimeout(() => {
        update("processing");
        setTimeout(() => {
          update("done");
          toast.success("Upload successful", { description: "Thumbnails and tags are being generated." });
        }, 1200);
      }, 1000);
    }, 800);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files?.length) addFiles(e.dataTransfer.files);
  };

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm text-muted-foreground">Library / Upload</p>
        <h1>Upload media</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Upload wildlife images and videos. Duplicates are automatically detected using file checksums.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-1 border-border">
          <CardContent className="p-5">
            <div
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={onDrop}
              className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
                dragOver ? "border-primary bg-secondary" : "border-border bg-accent/40"
              }`}
            >
              <div className="h-14 w-14 mx-auto rounded-full bg-secondary text-primary flex items-center justify-center">
                <UploadCloud className="h-7 w-7" />
              </div>
              <p className="mt-3 text-sm text-foreground">Drop files here or click to browse</p>
              <p className="text-xs text-muted-foreground mt-1">Supports JPG, PNG, MP4, MOV up to 100MB</p>
              <Button className="mt-4" onClick={() => inputRef.current?.click()}>Choose files</Button>
              <input
                ref={inputRef}
                type="file"
                multiple
                accept="image/*,video/*"
                className="hidden"
                onChange={(e) => e.target.files && addFiles(e.target.files)}
              />
            </div>
            <p className="text-xs text-muted-foreground mt-4">
              Tip: name a file with "dup" in it to preview duplicate detection.
            </p>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2 border-border">
          <CardContent className="p-0">
            <div className="px-5 py-4 border-b border-border flex items-center justify-between">
              <h3 className="text-foreground">Selected files</h3>
              <span className="text-xs text-muted-foreground">{files.length} item{files.length !== 1 ? "s" : ""}</span>
            </div>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>File name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {files.map((f) => (
                  <TableRow key={f.id} className={f.status === "duplicate" ? "bg-amber-50/50" : ""}>
                    <TableCell className="flex items-center gap-2">
                      {f.type.startsWith("video") ? <FileVideo className="h-4 w-4 text-muted-foreground" /> : <FileImage className="h-4 w-4 text-muted-foreground" />}
                      <span className="text-sm">{f.name}</span>
                    </TableCell>
                    <TableCell><Badge variant="outline" className="text-xs">{f.type.split("/")[1] ?? f.type}</Badge></TableCell>
                    <TableCell className="text-sm text-muted-foreground">{formatSize(f.size)}</TableCell>
                    <TableCell>{statusBadge(f.status)}</TableCell>
                  </TableRow>
                ))}
                {files.length === 0 && (
                  <TableRow><TableCell colSpan={4} className="text-center text-sm text-muted-foreground py-8">No files selected yet.</TableCell></TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      <Card className="border-border">
        <CardContent className="p-5">
          <h3 className="mb-4">Recent uploads</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {SAMPLE_MEDIA.slice(0, 6).map((m) => (
              <MediaCard key={m.id} media={m} />
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
