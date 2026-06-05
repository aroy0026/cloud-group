import { createContext, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import type { Media } from "./components/MediaCard";
import { api } from "./api";
import { useAuth } from "./auth";

export type MediaItem = Media & {
  fullUrl: string;
  checksum?: string;
  createdAt: string;
  size?: number;
  mimeType?: string;
  status?: string;
  error?: string;
  source: "seed" | "upload";
};

export type TagCondition = {
  tag: string;
  minCount: number;
};

export type NotificationSettings = {
  emailOn: boolean;
  thumbOn: boolean;
};

type MediaLibraryCtx = {
  media: MediaItem[];
  subscriptions: string[];
  notificationSettings: NotificationSettings;
  hasChecksum: (checksum: string) => boolean;
  refreshMedia: () => Promise<void>;
  uploadMedia: (input: {
    file: File;
    checksum: string;
    dataUrl?: string;
  }) => Promise<{ duplicate: boolean; file: MediaItem | null }>;
  addUploadedMedia: (input: {
    name: string;
    mimeType: string;
    size: number;
    checksum: string;
    dataUrl?: string;
  }) => MediaItem;
  searchByTags: (conditions: TagCondition[]) => MediaItem[] | Promise<MediaItem[]>;
  searchBySpecies: (species: string) => MediaItem[] | Promise<MediaItem[]>;
  searchByThumbnail: (thumbnailUrl: string) => MediaItem[] | Promise<MediaItem[]>;
  searchByFile: (file: File) => Promise<MediaItem[]>;
  addTags: (ids: string[], tags: string[]) => Promise<void>;
  removeTags: (ids: string[], tags: string[]) => Promise<void>;
  deleteMedia: (ids: string[]) => Promise<void>;
  addSubscription: (tag: string) => Promise<boolean>;
  removeSubscription: (tag: string) => Promise<void>;
  setNotificationSettings: (settings: NotificationSettings) => Promise<void>;
};

const MEDIA_STORAGE_KEY = "ecolens_media_v1";
const SUB_STORAGE_KEY = "ecolens_subscriptions_v1";
const SETTINGS_STORAGE_KEY = "ecolens_notification_settings_v1";
const MEDIA_REFRESH_MS = 60_000;

const VIDEO_THUMBNAIL = "";

const KNOWN_TAGS = [
  "koala",
  "kangaroo",
  "wombat",
  "dingo",
  "echidna",
  "joey",
  "tree",
  "grass",
  "outback",
  "bird",
  "possum",
  "wallaby",
];

const Ctx = createContext<MediaLibraryCtx | null>(null);

export function MediaLibraryProvider({ children }: { children: ReactNode }) {
  const { token, email } = useAuth();
  const [media, setMedia] = useState<MediaItem[]>([]);
  const [subscriptions, setSubscriptions] = useState<string[]>([]);
  const [notificationSettings, setNotificationSettingsState] =
    useState<NotificationSettings>(loadNotificationSettings);
  const mediaRef = useRef(media);

  useEffect(() => {
    mediaRef.current = media;
  }, [media]);

  useEffect(() => {
    if (!api.enabled || !token) return;

    refreshMedia({ includePendingDetails: false });
    api.listSubscriptions(token)
      .then((data) => {
        if (data.tags) {
          setSubscriptions(data.tags);
          save(SUB_STORAGE_KEY, data.tags);
        }
        if (data.settings) {
          setNotificationSettingsState(data.settings);
          save(SETTINGS_STORAGE_KEY, data.settings);
        }
      })
      .catch(() => undefined);
  }, [token]);

  useEffect(() => {
    if (!api.enabled || !token) return;
    const hasActiveProcessing = media.some((item) => shouldPoll(item));
    if (!hasActiveProcessing) return;

    let cancelled = false;
    const poll = async () => {
      if (cancelled) return;
      await refreshMedia({ includePendingDetails: false });
    };

    const interval = window.setInterval(poll, MEDIA_REFRESH_MS);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [media.some((item) => shouldPoll(item)), token]);

  const persistMedia = (updater: MediaItem[] | ((current: MediaItem[]) => MediaItem[])) => {
    setMedia((current) => {
      const next = typeof updater === "function" ? updater(current) : updater;
      return next;
    });
  };

  const hasChecksum = (checksum: string) => media.some((item) => item.checksum === checksum);

  const refreshMedia = async (options: { includePendingDetails?: boolean } = {}) => {
    if (!api.enabled || !token) return;
    const listed = await api.listMedia(token).catch(() => []);
    if (listed.length) {
      persistMedia((current) => mergeListedMedia(current, listed));
    }
    if (!options.includePendingDetails) return;
    const currentUploads = listed.length ? mergeListedMedia(mediaRef.current, listed) : mediaRef.current;
    const updates = await Promise.all(
      currentUploads
        .filter((item) => item.source === "upload")
        .map((item) =>
          api.getMedia(item.id, token)
            .then((fresh) => (fresh ? mergeMediaItem(item, fresh) : null))
            .catch(() => null)
        )
    );
    const ready = updates.filter(Boolean) as MediaItem[];
    if (ready.length) persistMedia((current) => mergeUpdatedMedia(current, ready));
  };

  const uploadMedia: MediaLibraryCtx["uploadMedia"] = async (input) => {
    if (api.enabled && token) {
      const result = await api.uploadMedia({
        file: input.file,
        checksum: input.checksum,
        token,
      });
      if (result.file) {
        const uploaded = mergeMediaItem(
          {
            id: result.file.id,
            name: input.file.name,
            type: input.file.type.startsWith("video") ? "video" : "image",
            thumbnail: input.file.type.startsWith("image") && input.dataUrl ? input.dataUrl : "",
            fullUrl: input.dataUrl ?? "",
            tags: [],
            checksum: input.checksum,
            createdAt: new Date().toISOString(),
            size: input.file.size,
            mimeType: input.file.type || "application/octet-stream",
            status: "PROCESSING",
            source: "upload",
          },
          result.file
        );
        persistMedia((current) => {
          const rest = current.filter((item) => item.id !== uploaded.id);
          return [uploaded, ...rest];
        });
      }
      return result;
    }

    if (hasChecksum(input.checksum)) return { duplicate: true, file: null };

    const item = addUploadedMedia({
      name: input.file.name,
      mimeType: input.file.type || "application/octet-stream",
      size: input.file.size,
      checksum: input.checksum,
      dataUrl: input.dataUrl,
    });
    return { duplicate: false, file: item };
  };

  const addUploadedMedia: MediaLibraryCtx["addUploadedMedia"] = (input) => {
    const type = input.mimeType.startsWith("video") ? "video" : "image";
    const item: MediaItem = {
      id: `media-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      name: input.name,
      type,
      thumbnail: type === "image" && input.dataUrl ? input.dataUrl : "",
      fullUrl: input.dataUrl ?? "",
      tags: inferTags(input.name),
      checksum: input.checksum,
      status: "READY",
      createdAt: new Date().toISOString(),
      size: input.size,
      mimeType: input.mimeType,
      source: "upload",
    };
    persistMedia((current) => [item, ...current]);
    return item;
  };

  const searchByTags = (conditions: TagCondition[]) => {
    if (api.enabled && token) return api.searchByTags(conditions, token);

    const cleaned = conditions
      .map((c) => ({ tag: cleanTag(c.tag), minCount: Math.max(1, c.minCount || 1) }))
      .filter((c) => c.tag);

    return media.filter((item) =>
      cleaned.every((condition) => {
        const tag = item.tags.find((t) => cleanTag(t.name) === condition.tag);
        return !!tag && tag.count >= condition.minCount;
      })
    );
  };

  const searchBySpecies = (species: string) => {
    if (api.enabled && token) return api.searchBySpecies(species, token);

    const q = cleanTag(species);
    if (!q) return [];
    return media.filter((item) => item.tags.some((tag) => cleanTag(tag.name).includes(q)));
  };

  const searchByThumbnail = (thumbnailUrl: string) => {
    if (api.enabled && token) return api.searchByThumbnail(thumbnailUrl, token);

    const q = thumbnailUrl.trim();
    if (!q) return [];
    return media.filter((item) => item.thumbnail === q || item.fullUrl === q);
  };

  const searchByFile = async (file: File) => {
    if (api.enabled && token) return api.searchByFile(file, token);

    const checksum = await calculateFileChecksum(file);
    const duplicate = media.find((item) => item.checksum === checksum);
    if (duplicate) return [duplicate];

    const tags = inferTags(file.name);
    const names = tags.map((tag) => tag.name);
    if (!names.length) {
      return media.filter((item) => item.type === (file.type.startsWith("video") ? "video" : "image"));
    }

    return media.filter((item) =>
      names.every((name) => item.tags.some((tag) => cleanTag(tag.name) === name))
    );
  };

  const addTags = async (ids: string[], tags: string[]) => {
    const cleaned = uniqueTags(tags);
    if (!ids.length || !cleaned.length) return;
    if (api.enabled && token) {
      const urls = media.filter((item) => ids.includes(item.id)).map((item) => item.fullUrl).filter(Boolean);
      const updated = await api.bulkEditTags({ ids, urls, tags: cleaned, operation: 1 }, token);
      persistMedia((current) => mergeUpdatedMedia(current, updated));
      return;
    }

    persistMedia((current) =>
      current.map((item) => {
        if (!ids.includes(item.id)) return item;
        const nextTags = item.tags.map((tag) => ({ ...tag }));
        cleaned.forEach((name) => {
          const existing = nextTags.find((tag) => cleanTag(tag.name) === name);
          if (existing) existing.count += 1;
          else nextTags.push({ name, count: 1 });
        });
        return { ...item, tags: nextTags };
      })
    );
  };

  const removeTags = async (ids: string[], tags: string[]) => {
    const cleaned = uniqueTags(tags);
    if (!ids.length || !cleaned.length) return;
    if (api.enabled && token) {
      const urls = media.filter((item) => ids.includes(item.id)).map((item) => item.fullUrl).filter(Boolean);
      const updated = await api.bulkEditTags({ ids, urls, tags: cleaned, operation: 0 }, token);
      persistMedia((current) => mergeUpdatedMedia(current, updated));
      return;
    }

    persistMedia((current) =>
      current.map((item) =>
        ids.includes(item.id)
          ? { ...item, tags: item.tags.filter((tag) => !cleaned.includes(cleanTag(tag.name))) }
          : item
      )
    );
  };

  const deleteMedia = async (ids: string[]) => {
    if (!ids.length) return;
    if (api.enabled && token) {
      const urls = media.filter((item) => ids.includes(item.id)).map((item) => item.fullUrl).filter(Boolean);
      await api.deleteFiles({ ids, urls }, token);
    }
    persistMedia((current) => current.filter((item) => !ids.includes(item.id)));
  };

  const addSubscription = async (tag: string) => {
    const cleaned = cleanTag(tag);
    if (!cleaned || subscriptions.includes(cleaned)) return false;
    if (api.enabled && token) {
      const data = await api.addSubscription(cleaned, token, email ?? '');
      const next = data.tags ?? [...subscriptions, cleaned];
      setSubscriptions(next);
      save(SUB_STORAGE_KEY, next);
      return true;
    }

    const next = [...subscriptions, cleaned];
    setSubscriptions(next);
    save(SUB_STORAGE_KEY, next);
    return true;
  };

  const removeSubscription = async (tag: string) => {
    const cleaned = cleanTag(tag);
    if (api.enabled && token) {
      const data = await api.removeSubscription(cleaned, token);
      const next = data.tags ?? subscriptions.filter((item) => item !== cleaned);
      setSubscriptions(next);
      save(SUB_STORAGE_KEY, next);
      return;
    }

    const next = subscriptions.filter((item) => item !== cleaned);
    setSubscriptions(next);
    save(SUB_STORAGE_KEY, next);
  };

  const setNotificationSettings = async (settings: NotificationSettings) => {
    if (api.enabled && token) {
      const data = await api.updateNotificationSettings(settings, token);
      const next = data.settings ?? settings;
      setNotificationSettingsState(next);
      save(SETTINGS_STORAGE_KEY, next);
      return;
    }

    setNotificationSettingsState(settings);
    save(SETTINGS_STORAGE_KEY, settings);
  };

  const value = useMemo(
    () => ({
      media,
      subscriptions,
      notificationSettings,
      hasChecksum,
      refreshMedia,
      uploadMedia,
      addUploadedMedia,
      searchByTags,
      searchBySpecies,
      searchByThumbnail,
      searchByFile,
      addTags,
      removeTags,
      deleteMedia,
      addSubscription,
      removeSubscription,
      setNotificationSettings,
    }),
    [media, subscriptions, notificationSettings, token]
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useMediaLibrary() {
  const value = useContext(Ctx);
  if (!value) throw new Error("useMediaLibrary must be used within MediaLibraryProvider");
  return value;
}

export async function calculateFileChecksum(file: File) {
  const buffer = await file.arrayBuffer();
  const digest = await crypto.subtle.digest("SHA-256", buffer);
  return Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

export function readImageAsDataUrl(file: File) {
  if (!file.type.startsWith("image")) return Promise.resolve(undefined);
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

function loadMedia(): MediaItem[] {
  return [];
}

function loadSubscriptions() {
  return load<string[]>(SUB_STORAGE_KEY) ?? [];
}

function loadNotificationSettings() {
  return load<NotificationSettings>(SETTINGS_STORAGE_KEY) ?? { emailOn: true, thumbOn: false };
}

function load<T>(key: string) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}

function save<T>(key: string, value: T) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // The demo keeps working in memory if browser storage is unavailable.
  }
}

function inferTags(name: string) {
  const lower = name.toLowerCase();
  const tags = KNOWN_TAGS.filter((tag) => lower.includes(tag)).map((tag) => ({ name: tag, count: 1 }));
  return tags.length ? tags : [{ name: "untagged", count: 1 }];
}

function uniqueTags(tags: string[]) {
  return Array.from(new Set(tags.map(cleanTag).filter(Boolean)));
}

function cleanTag(tag: string) {
  return tag.trim().toLowerCase();
}

function mergeUpdatedMedia(current: MediaItem[], updated: MediaItem[]) {
  if (!updated.length) return current;
  const byId = new Map(updated.map((item) => [item.id, item]));
  return current.map((item) => {
    const fresh = byId.get(item.id);
    return fresh ? mergeMediaItem(item, fresh) : item;
  });
}

function mergeListedMedia(current: MediaItem[], listed: MediaItem[]) {
  const byId = new Map(current.map((item) => [item.id, item]));
  const merged = listed.map((item) => {
    const existing = byId.get(item.id);
    return existing ? mergeMediaItem(existing, item) : item;
  });
  const listedIds = new Set(listed.map((item) => item.id));
  const localOnly = current.filter((item) => item.source !== "upload" || !listedIds.has(item.id));
  return [...merged, ...localOnly];
}

function mergeMediaItem(current: MediaItem, fresh: MediaItem): MediaItem {
  return {
    ...current,
    ...fresh,
    thumbnail: fresh.thumbnail || current.thumbnail,
    fullUrl: fresh.fullUrl || current.fullUrl,
    tags: fresh.tags.length ? fresh.tags : current.tags,
    checksum: fresh.checksum ?? current.checksum,
    createdAt: fresh.createdAt ?? current.createdAt,
    size: fresh.size ?? current.size,
    mimeType: fresh.mimeType ?? current.mimeType,
    source: "upload",
  };
}

function shouldPoll(item: MediaItem) {
  if (item.source !== "upload") return false;
  const status = (item.status || "").toUpperCase();
  return !["READY", "FAILED", "ERROR", "DELETED"].includes(status);
}
