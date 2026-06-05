import { ExternalLink } from "lucide-react";
import type { MediaItem } from "../media-library";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./ui/dialog";
import { ImageWithFallback } from "./figma/ImageWithFallback";

export function MediaPreviewDialog({
  media,
  onClose,
}: {
  media: MediaItem | null;
  onClose: () => void;
}) {
  return (
    <Dialog open={!!media} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-3xl">
        {media && (
          <>
            <DialogHeader>
              <DialogTitle>{media.name}</DialogTitle>
            </DialogHeader>
            <div className="rounded-lg overflow-hidden bg-muted aspect-video">
              <ImageWithFallback src={media.thumbnail} alt={media.name} className="w-full h-full object-cover" />
            </div>
            <div className="flex flex-wrap gap-1 mt-3">
              {media.tags.length ? (
                media.tags.map((tag) => (
                  <Badge key={tag.name} variant="secondary">
                    {tag.name} x{tag.count}
                  </Badge>
                ))
              ) : (
                <Badge variant="outline">tags pending</Badge>
              )}
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm mt-3">
              <div>
                <span className="text-muted-foreground">Type:</span> {media.type}
              </div>
              <div>
                <span className="text-muted-foreground">Status:</span> {media.status ?? "READY"}
              </div>
            </div>
            <Button
              className="mt-3 w-fit"
              variant={media.type === "image" ? "outline" : "default"}
              onClick={() => window.open(media.fullUrl || media.thumbnail, "_blank", "noopener,noreferrer")}
              disabled={!media.fullUrl && !media.thumbnail}
            >
              <ExternalLink className="mr-2 h-4 w-4" />
              {media.type === "video" ? "Open video URL" : "Open full-size image"}
            </Button>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
