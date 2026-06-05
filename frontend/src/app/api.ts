import type { MediaItem, NotificationSettings, TagCondition } from "./media-library";
import { cognitoGetCurrentIdToken } from "./cognito";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export const apiEnabled = API_BASE_URL.length > 0 && !API_BASE_URL.includes("your-api-gateway");

export type AuthSession = {
  email: string;
  token: string;
};

type RequestOptions = {
  method?: string;
  token?: string | null;
  body?: unknown;
  headers?: HeadersInit;
};

type AssignmentMedia = {
  mediaId?: string;
  fileKind?: string;
  originalName?: string;
  contentType?: string;
  tags?: Record<string, number>;
  tagList?: string[];
  thumbnailUrl?: string;
  fullUrl?: string;
  canonicalThumbnailUrl?: string;
  canonicalFullUrl?: string;
  status?: string;
  error?: string;
};

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export const api = {
  enabled: apiEnabled,

  signUp() {
    throw new ApiError("Sign-up is handled directly by Cognito, not API Gateway.", 400);
  },

  signIn() {
    throw new ApiError("Sign-in is handled directly by Cognito, not API Gateway.", 400);
  },

  signOut() {
    return Promise.resolve();
  },

  listMedia(token: string) {
    return request<unknown[]>("/files", { token }).then((items) => items.map(normalizeMediaItem));
  },

  async uploadMedia(input: {
    file: File;
    checksum: string;
    token: string;
  }) {
    const { file, checksum, token } = input;
    const prepared = await request<{
      duplicate?: boolean;
      file?: unknown;
      fileId?: string;
      mediaId?: string;
      uploadUrl?: string;
      headers?: Record<string, string>;
      fields?: Record<string, string>;
      message?: string;
    }>("/upload/prepare", {
      method: "POST",
      token,
      body: {
        name: file.name,
        mimeType: file.type || "application/octet-stream",
        size: file.size,
        checksum,
      },
    });

    if (prepared.duplicate) {
      return { duplicate: true, file: prepared.file ? normalizeMediaItem(prepared.file) : null };
    }

    const fileId = prepared.fileId ?? prepared.mediaId;
    if (!prepared.uploadUrl || !fileId) {
      throw new ApiError(prepared.message || "Upload URL missing from presign response.", 500);
    }

    if (prepared.fields) {
      const form = new FormData();
      Object.entries(prepared.fields).forEach(([key, value]) => form.append(key, value));
      form.append("file", file);
      await uploadToSignedUrl(prepared.uploadUrl, { method: "POST", body: form });
    } else {
      await uploadToSignedUrl(prepared.uploadUrl, {
        method: "PUT",
        headers: prepared.headers ?? { "Content-Type": file.type || "application/octet-stream" },
        body: file,
      });
    }

    const completed = await request<unknown>("/upload/complete", {
      method: "POST",
      token,
      body: {
        fileId,
        name: file.name,
        mimeType: file.type || "application/octet-stream",
        size: file.size,
        checksum,
      },
    });

    if (completed && typeof completed === "object" && "duplicate" in completed) {
      const result = completed as { duplicate?: boolean; file?: unknown };
      return {
        duplicate: Boolean(result.duplicate),
        file: result.file ? normalizeMediaItem(result.file) : null,
      };
    }

    return { duplicate: false, file: normalizeMediaItem(completed) };
  },

  async getMedia(mediaId: string, token: string) {
    const items = await this.listMedia(token);
    return items.find((item) => item.id === mediaId) ?? null;
  },

  searchByTags(conditions: TagCondition[], token: string) {
    const tags = Object.fromEntries(
      conditions
        .map((condition) => [cleanTag(condition.tag), Math.max(1, Number(condition.minCount) || 1)] as const)
        .filter(([tag]) => tag)
    );
    return request<unknown[]>("/query/by-tags", {
      method: "POST",
      token,
      body: {
        conditions: Object.entries(tags).map(([tag, minCount]) => ({ tag, minCount })),
      },
    }).then((items) => items.map(normalizeMediaItem));
  },

  searchBySpecies(species: string, token: string) {
    return request<unknown[]>("/query/by-species", {
      method: "POST",
      token,
      body: { species: cleanTag(species) },
    }).then((items) => items.map(normalizeMediaItem));
  },

  searchByThumbnail(thumbnailUrl: string, token: string) {
    return request<unknown[]>("/query/by-thumbnail", {
      method: "POST",
      token,
      body: { thumbnailUrl },
    }).then((items) => items.map(normalizeMediaItem));
  },

  searchByFile(file: File, token: string) {
    return request<unknown[]>("/query/by-file", {
      method: "POST",
      token,
      body: file,
      headers: { "Content-Type": file.type || "application/octet-stream" },
    }).then((items) => items.map(normalizeMediaItem));
  },

  bulkEditTags(input: { ids: string[]; urls: string[]; tags: string[]; operation: 0 | 1 }, token: string) {
    return request<unknown[]>("/tags/bulk-edit", {
      method: "POST",
      token,
      body: input,
    }).then((items) => items.map(normalizeMediaItem));
  },

  deleteFiles(input: { ids: string[]; urls: string[] }, token: string) {
    return request<{ deletedIds?: string[] }>("/files/delete", {
      method: "POST",
      token,
      body: input,
    });
  },

  listSubscriptions(token: string) {
    return request<{ tags?: string[]; settings?: NotificationSettings }>("/notifications/subscriptions", {
      token,
    });
  },

  addSubscription(tag: string, token: string) {
    return request<{ tags?: string[]; message?: string }>("/notifications/subscriptions", {
      method: "POST",
      token,
      body: { tag: cleanTag(tag) },
    });
  },

  removeSubscription(tag: string, token: string) {
    return request<{ tags?: string[] }>("/notifications/subscriptions", {
      method: "DELETE",
      token,
      body: { tag: cleanTag(tag) },
    });
  },

  updateNotificationSettings(settings: NotificationSettings, token?: string | null) {
    return request<{ settings?: NotificationSettings }>("/notifications/settings", {
      method: "PUT",
      token,
      body: settings,
    });
  },
};

async function request<T>(path: string, options: RequestOptions = {}) {
  if (!API_BASE_URL) {
    throw new ApiError("API base URL is not configured. Set VITE_API_BASE_URL.", 0);
  }

  const headers = new Headers(options.headers);
  const body = options.body;
  if (!(body instanceof File) && body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const token = (await cognitoGetCurrentIdToken().catch(() => null)) ?? options.token;
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers,
    body: body instanceof File ? body : body === undefined ? undefined : JSON.stringify(body),
  });

  const text = await response.text();
  const payload = text ? safeJson(text) : null;
  if (!response.ok) {
    throw new ApiError(errorMessage(payload) ?? response.statusText, response.status);
  }

  return payload as T;
}

function normalizeMediaItem(raw: unknown): MediaItem {
  const item = (raw ?? {}) as Record<string, unknown>;
  const id = stringValue(item.mediaId) ?? stringValue(item.id) ?? stringValue(item.fileId) ?? crypto.randomUUID();
  const fullUrl =
    stringValue(item.fullUrl) ??
    stringValue(item.canonicalFullUrl) ??
    stringValue(item.url) ??
    stringValue(item.fileUrl) ??
    "";
  const thumbnail =
    stringValue(item.thumbnailUrl) ??
    stringValue(item.canonicalThumbnailUrl) ??
    stringValue(item.thumbnail) ??
    stringValue(item.thumbUrl) ??
    fullUrl;
  const mimeType = stringValue(item.contentType) ?? stringValue(item.mimeType);
  const fileKind = stringValue(item.fileKind);
  const inferredType = mimeType?.startsWith("video") || fileKind === "video" ? "video" : "image";

  return {
    id,
    name: stringValue(item.originalName) ?? stringValue(item.name) ?? stringValue(item.filename) ?? id,
    type: inferredType,
    thumbnail,
    fullUrl,
    tags: normalizeTags(item.tags),
    checksum: stringValue(item.sha256) ?? stringValue(item.checksum),
    createdAt: stringValue(item.createdAt) ?? stringValue(item.updatedAt) ?? new Date().toISOString(),
    size: numberValue(item.size),
    mimeType,
    status: stringValue(item.status),
    error: stringValue(item.error),
    source: "upload",
  };
}

async function uploadToSignedUrl(url: string, init: RequestInit) {
  const response = await fetch(url, init);
  if (!response.ok) {
    throw new ApiError(`Signed upload failed: ${response.statusText}`, response.status);
  }
}

function normalizeTags(raw: unknown) {
  if (Array.isArray(raw)) {
    return raw.map((tag) => {
      if (typeof tag === "string") return { name: tag, count: 1 };
      const value = tag as Record<string, unknown>;
      return {
        name: stringValue(value.name) ?? stringValue(value.tag) ?? "untagged",
        count: numberValue(value.count) ?? 1,
      };
    });
  }

  if (raw && typeof raw === "object") {
    return Object.entries(raw as Record<string, unknown>).map(([name, count]) => ({
      name,
      count: Number(count) || 1,
    }));
  }

  return [];
}

function safeJson(text: string) {
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function errorMessage(payload: unknown) {
  if (typeof payload === "string") return payload;
  if (payload && typeof payload === "object") {
    const body = payload as Record<string, unknown>;
    return stringValue(body.message) ?? stringValue(body.error);
  }
  return null;
}

function cleanTag(value: string) {
  return value.trim().toLowerCase().replace(/\s+/g, "_");
}

function stringValue(value: unknown) {
  return typeof value === "string" && value.length ? value : undefined;
}

function numberValue(value: unknown) {
  return typeof value === "number" ? value : undefined;
}
