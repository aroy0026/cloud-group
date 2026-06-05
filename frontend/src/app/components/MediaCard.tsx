import { Badge } from "./ui/badge";
import { Checkbox } from "./ui/checkbox";
import { ImageWithFallback } from "./figma/ImageWithFallback";
import { Image as ImageIcon, Video, Play } from "lucide-react";

export type Media = {
  id: string;
  name: string;
  type: "image" | "video";
  thumbnail: string;
  tags: { name: string; count: number }[];
  status?: string;
  error?: string;
};

export function MediaCard({
  media,
  selected,
  onToggle,
  onOpen,
  showCheckbox = false,
}: {
  media: Media;
  selected?: boolean;
  onToggle?: (id: string) => void;
  onOpen?: (m: Media) => void;
  showCheckbox?: boolean;
}) {
  return (
    <div className="group relative bg-card border border-border rounded-lg overflow-hidden hover:shadow-md transition-shadow">
      <button onClick={() => onOpen?.(media)} className="block w-full text-left">
        <div className="relative aspect-[4/3] bg-muted overflow-hidden">
          <ImageWithFallback
            src={media.thumbnail}
            alt={media.name}
            className="w-full h-full object-cover"
          />
          {media.type === "video" && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/20">
              <div className="h-10 w-10 rounded-full bg-black/60 text-white flex items-center justify-center">
                <Play className="h-5 w-5" />
              </div>
            </div>
          )}
          <div className="absolute top-2 left-2 bg-white/90 backdrop-blur rounded-md px-1.5 py-0.5 flex items-center gap-1 text-xs">
            {media.type === "video" ? <Video className="h-3 w-3" /> : <ImageIcon className="h-3 w-3" />}
            <span className="capitalize">{media.type}</span>
          </div>
          {media.status && (
            <div className={`absolute bottom-2 left-2 rounded-md px-1.5 py-0.5 text-xs ${statusClass(media.status)}`}>
              {labelStatus(media.status)}
            </div>
          )}
        </div>
      </button>
      {showCheckbox && (
        <div className="absolute top-2 right-2 bg-white/90 backdrop-blur rounded p-1">
          <Checkbox checked={!!selected} onCheckedChange={() => onToggle?.(media.id)} />
        </div>
      )}
      <div className="p-3 space-y-2">
        <div className="text-sm truncate text-foreground" title={media.name}>{media.name}</div>
        <div className="flex flex-wrap gap-1">
          {media.tags.length ? media.tags.map((t) => (
            <Badge key={t.name} variant="secondary" className="text-xs">
              {t.name} ×{t.count}
            </Badge>
          )) : (
            <Badge variant="outline" className="text-xs">tags pending</Badge>
          )}
        </div>
        {media.error && <p className="text-xs text-red-700 line-clamp-2">{media.error}</p>}
      </div>
    </div>
  );
}

function labelStatus(status: string) {
  const upper = status.toUpperCase();
  if (upper === "READY") return "Ready";
  if (upper === "FAILED" || upper === "ERROR") return "Failed";
  if (upper === "PRESIGNED") return "Upload reserved";
  if (upper === "QUEUED") return "Queued";
  return "Processing";
}

function statusClass(status: string) {
  const upper = status.toUpperCase();
  if (upper === "READY") return "bg-emerald-50 text-emerald-700 border border-emerald-200";
  if (upper === "FAILED" || upper === "ERROR") return "bg-red-50 text-red-700 border border-red-200";
  return "bg-violet-50 text-violet-700 border border-violet-200";
}
