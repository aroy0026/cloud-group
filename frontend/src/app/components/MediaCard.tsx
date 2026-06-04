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
          {media.tags.map((t) => (
            <Badge key={t.name} variant="secondary" className="text-xs">
              {t.name} ×{t.count}
            </Badge>
          ))}
        </div>
      </div>
    </div>
  );
}
