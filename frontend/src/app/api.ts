import type { MediaItem, NotificationSettings, TagCondition } from "./media-library";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export const apiEnabled = API_BASE_URL.length > 0;

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

  signUp(input: { firstName: string; lastName: string; email: string; password: string }) {
    return request<{ message?: string }>("/auth/sign-up", {
      method: "POST",
      body: input,
    });
  },

  signIn(input: { email: string; password: string }) {
    return request<AuthSession | { accessToken: string; idToken?: string; email?: string }>("/auth/sign-in", {
      method: "POST",
      body: input,
    }).then((session) => ({
      email: session.email ?? input.email,
      token: "token" in session ? session.token : session.idToken ?? session.accessToken,
    }));
  },

  signOut(token: string | null) {
    if (!token) return Promise.resolve();
    return request<void>("/auth/sign-out", {
      method: "POST",
      token,
    }).catch(() => undefined);
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
      uploadUrl?: string;
      headers?: Record<string, string>;
      fields?: Record<string, string>;
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

    if (prepared.uploadUrl) {
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
          fileId: prepared.fileId,
          name: file.name,
          mimeType: file.type || "application/octet-stream",
          size: file.size,
          checksum,
        },
      });

      return { duplicate: false, file: normalizeMediaItem(completed) };
    }

    const form = new FormData();
    form.append("file", file);
    form.append("checksum", checksum);
    const uploaded = await request<unknown>("/upload", {
      method: "POST",
      token,
      body: form,
    });
    return { duplicate: false, file: normalizeMediaItem(uploaded) };
  },

  searchByTags(conditions: TagCondition[], token: string) {
    return request<unknown[]>("/query/by-tags", {
      method: "POST",
      token,
      body: { conditions },
    }).then((items) => items.map(normalizeMediaItem));
  },

  searchBySpecies(species: string, token: string) {
    return request<unknown[]>("/query/by-species", {
      method: "POST",
      token,
      body: { species },
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
    const form = new FormData();
    form.append("file", file);
    return request<unknown[]>("/query/by-file", {
      method: "POST",
      token,
      body: form,
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
    return request<{ tags?: string[] }>("/notifications/subscriptions", {
      method: "POST",
      token,
      body: { tag },
    });
  },

  removeSubscription(tag: string, token: string) {
    return request<{ tags?: string[] }>("/notifications/subscriptions", {
      method: "DELETE",
      token,
      body: { tag },
    });
  },

  updateNotificationSettings(settings: NotificationSettings, token: string) {
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

  const isForm = options.body instanceof FormData;
  const headers = new Headers(options.headers);
  if (!isForm && options.body !== undefined) headers.set("Content-Type", "application/json");
  if (options.token) headers.set("Authorization", `Bearer ${options.token}`);

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers,
    body: isForm ? options.body : options.body === undefined ? undefined : JSON.stringify(options.body),
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
  const fullUrl = stringValue(item.fullUrl) ?? stringValue(item.url) ?? stringValue(item.fileUrl) ?? "";
  const thumbnail =
    stringValue(item.thumbnail) ?? stringValue(item.thumbnailUrl) ?? stringValue(item.thumbUrl) ?? fullUrl;
  const mimeType = stringValue(item.mimeType) ?? stringValue(item.contentType);
  const inferredType = mimeType?.startsWith("video") || stringValue(item.type) === "video" ? "video" : "image";

  return {
    id: stringValue(item.id) ?? stringValue(item.fileId) ?? fullUrl,
    name: stringValue(item.name) ?? stringValue(item.filename) ?? "Untitled media",
    type: inferredType,
    thumbnail,
    fullUrl,
    tags: normalizeTags(item.tags),
    checksum: stringValue(item.checksum),
    createdAt: stringValue(item.createdAt) ?? stringValue(item.timestamp) ?? new Date().toISOString(),
    size: numberValue(item.size),
    mimeType,
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

function stringValue(value: unknown) {
  return typeof value === "string" && value.length ? value : undefined;
}

function numberValue(value: unknown) {
  return typeof value === "number" ? value : undefined;
}
