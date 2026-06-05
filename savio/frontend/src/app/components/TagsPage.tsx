import { useState } from "react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Switch } from "./ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription,
} from "./ui/dialog";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from "./ui/alert-dialog";
import { Loader2, Plus, Search, Trash2, TagIcon, BellRing, X } from "lucide-react";
import { toast } from "sonner";
import { MediaCard } from "./MediaCard";
import { useMediaLibrary } from "../media-library";

export function TagsPage() {
  const {
    media,
    subscriptions,
    notificationSettings,
    addTags,
    removeTags,
    deleteMedia,
    addSubscription,
    removeSubscription,
    setNotificationSettings,
  } = useMediaLibrary();
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [filter, setFilter] = useState("");
  const [type, setType] = useState("all");
  const [dateFilter, setDateFilter] = useState("any");
  const [addOpen, setAddOpen] = useState(false);
  const [removeOpen, setRemoveOpen] = useState(false);
  const [delOpen, setDelOpen] = useState(false);
  const [tagsInput, setTagsInput] = useState("");
  const [newSub, setNewSub] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  const filtered = media.filter((m) => {
    const matchesText = !filter ||
      m.name.toLowerCase().includes(filter.toLowerCase()) ||
      m.tags.some((t) => t.name.toLowerCase().includes(filter.toLowerCase()));
    const matchesType = type === "all" || m.type === type;
    const ageMs = Date.now() - new Date(m.createdAt).getTime();
    const matchesDate = dateFilter === "any"
      || (dateFilter === "7d" && ageMs <= 7 * 86_400_000)
      || (dateFilter === "30d" && ageMs <= 30 * 86_400_000);
    return matchesText && matchesType && matchesDate;
  });

  const selectedIds = Object.keys(selected).filter((k) => selected[k]);
  const toggle = (id: string) => setSelected((s) => ({ ...s, [id]: !s[id] }));

  const apply = async (mode: "add" | "remove") => {
    const tags = tagsInput.split(",").map((t) => t.trim()).filter(Boolean);
    if (!tags.length) { toast.error("Please enter at least one tag."); return; }
    setActionLoading(true);
    try {
      if (mode === "add") await addTags(selectedIds, tags);
      else await removeTags(selectedIds, tags);
      toast.success(
        mode === "add"
          ? `Tags successfully added to ${selectedIds.length} files`
          : `Tags successfully removed from ${selectedIds.length} files`
      );
      setTagsInput("");
      setAddOpen(false);
      setRemoveOpen(false);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Bulk tag edit failed.";
      toast.error("Tag update failed", { description: message });
    } finally {
      setActionLoading(false);
    }
  };

  const doDelete = async () => {
    setActionLoading(true);
    try {
      await deleteMedia(selectedIds);
      toast.success(`${selectedIds.length} files deleted`);
      setSelected({});
      setDelOpen(false);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Delete failed.";
      toast.error("Delete failed", { description: message });
    } finally {
      setActionLoading(false);
    }
  };

  const handleAddSubscription = async () => {
    const v = newSub.trim().toLowerCase();
    if (!v) {
      toast.error("Please enter a tag to subscribe to.");
      return;
    }
    setActionLoading(true);
    try {
      if (!await addSubscription(v)) {
        toast.warning("Already subscribed");
        return;
      }
      setNewSub("");
      toast.success(`Subscribed to "${v}"`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Subscription update failed.";
      toast.error("Subscription failed", { description: message });
    } finally {
      setActionLoading(false);
    }
  };

  const handleRemoveSubscription = async (tag: string) => {
    setActionLoading(true);
    try {
      await removeSubscription(tag);
      toast.success(`Unsubscribed from "${tag}"`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Subscription update failed.";
      toast.error("Subscription failed", { description: message });
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm text-muted-foreground">Library / Tags & notifications</p>
        <h1>Tags & notifications</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Bulk‑edit tags, delete media, and manage tag‑based email subscriptions.
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <Card className="xl:col-span-2 border-border">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2"><TagIcon className="h-5 w-5 text-primary" /> Tag management</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-col md:flex-row md:items-center gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Filter by filename or tag…"
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                />
              </div>
              <Select value={type} onValueChange={setType}>
                <SelectTrigger className="md:w-40"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All types</SelectItem>
                  <SelectItem value="image">Images</SelectItem>
                  <SelectItem value="video">Videos</SelectItem>
                </SelectContent>
              </Select>
              <Select value={dateFilter} onValueChange={setDateFilter}>
                <SelectTrigger className="md:w-40"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="any">Any date</SelectItem>
                  <SelectItem value="7d">Last 7 days</SelectItem>
                  <SelectItem value="30d">Last 30 days</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center justify-between border-t border-b border-border py-3">
              <p className="text-sm text-muted-foreground">
                {selectedIds.length} selected of {filtered.length} files
              </p>
              <div className="flex items-center gap-2">
                <Button size="sm" disabled={!selectedIds.length || actionLoading} onClick={() => setAddOpen(true)}>
                  <Plus className="mr-1.5 h-4 w-4" /> Add tags
                </Button>
                <Button size="sm" variant="outline" disabled={!selectedIds.length || actionLoading} onClick={() => setRemoveOpen(true)}>
                  Remove tags
                </Button>
                <Button size="sm" variant="destructive" disabled={!selectedIds.length || actionLoading} onClick={() => setDelOpen(true)}>
                  <Trash2 className="mr-1.5 h-4 w-4" /> Delete selected
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {filtered.map((m) => (
                <MediaCard
                  key={m.id}
                  media={m}
                  showCheckbox
                  selected={!!selected[m.id]}
                  onToggle={toggle}
                />
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="border-border h-fit">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2"><BellRing className="h-5 w-5 text-primary" /> Tag subscriptions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            <p className="text-sm text-muted-foreground">
              Receive email notifications when new media with these tags is added.
            </p>

            <div>
              <Label className="text-sm">Subscribed tags</Label>
              {subscriptions.length === 0 ? (
                <div className="mt-2 border border-dashed border-border rounded-lg p-5 text-center text-sm text-muted-foreground">
                  No subscriptions yet. Add a tag below to start getting alerts.
                </div>
              ) : (
                <div className="flex flex-wrap gap-2 mt-2">
                  {subscriptions.map((t) => (
                    <Badge key={t} variant="secondary" className="pl-2.5 pr-1 py-1 gap-1">
                      {t}
                      <button disabled={actionLoading} onClick={() => handleRemoveSubscription(t)}
                        className="rounded-full hover:bg-black/5 p-0.5">
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              )}
            </div>

            <div className="flex items-end gap-2">
              <div className="flex-1 space-y-1.5">
                <Label>Add subscription</Label>
                <Input placeholder="e.g. dingo" value={newSub} onChange={(e) => setNewSub(e.target.value)} disabled={actionLoading} />
              </div>
              <Button onClick={handleAddSubscription} disabled={actionLoading}>
                {actionLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Add
              </Button>
            </div>

            <div className="border-t border-border pt-4 space-y-3">
              <h4>Notification settings</h4>
              <div className="flex items-center justify-between">
                <Label htmlFor="email-on" className="font-normal text-sm">Email me when new media for my tags is uploaded</Label>
                <Switch
                  id="email-on"
                  checked={notificationSettings.emailOn}
                  disabled={actionLoading}
                  onCheckedChange={async (emailOn) => {
                    try {
                      await setNotificationSettings({ ...notificationSettings, emailOn });
                      toast.success("Notification settings saved");
                    } catch (err) {
                      const message = err instanceof Error ? err.message : "Could not save notification settings.";
                      toast.error("Settings update failed", { description: message });
                    }
                  }}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="thumb-on" className="font-normal text-sm">Include thumbnail previews in emails</Label>
                <Switch
                  id="thumb-on"
                  checked={notificationSettings.thumbOn}
                  disabled={actionLoading}
                  onCheckedChange={async (thumbOn) => {
                    try {
                      await setNotificationSettings({ ...notificationSettings, thumbOn });
                      toast.success("Notification settings saved");
                    } catch (err) {
                      const message = err instanceof Error ? err.message : "Could not save notification settings.";
                      toast.error("Settings update failed", { description: message });
                    }
                  }}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Dialog open={addOpen} onOpenChange={setAddOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add tags to {selectedIds.length} files</DialogTitle>
            <DialogDescription>Comma‑separated. Existing tags will have their counts incremented.</DialogDescription>
          </DialogHeader>
          <div className="space-y-1.5">
            <Label>Tags to add</Label>
            <Input placeholder="koala, eucalyptus" value={tagsInput} onChange={(e) => setTagsInput(e.target.value)} disabled={actionLoading} />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddOpen(false)} disabled={actionLoading}>Cancel</Button>
            <Button onClick={() => apply("add")} disabled={actionLoading}>
              {actionLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Apply to selected files
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={removeOpen} onOpenChange={setRemoveOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remove tags from {selectedIds.length} files</DialogTitle>
            <DialogDescription>For remove, tags not currently assigned will be ignored.</DialogDescription>
          </DialogHeader>
          <div className="space-y-1.5">
            <Label>Tags to remove</Label>
            <Input placeholder="grass, joey" value={tagsInput} onChange={(e) => setTagsInput(e.target.value)} disabled={actionLoading} />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRemoveOpen(false)} disabled={actionLoading}>Cancel</Button>
            <Button onClick={() => apply("remove")} disabled={actionLoading}>
              {actionLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Apply to selected files
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog open={delOpen} onOpenChange={setDelOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete {selectedIds.length} selected files?</AlertDialogTitle>
            <AlertDialogDescription>
              Both the full media and thumbnails will be permanently deleted, and the entries removed from the database. This cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={actionLoading}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={doDelete} disabled={actionLoading} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              {actionLoading ? "Deleting..." : "Delete permanently"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
