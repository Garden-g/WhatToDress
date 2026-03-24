import type {
  ApiEnvelope,
  ChatMessage,
  ChatResponseData,
  ForgottenItem,
  OutfitRecommendation,
  UploadDraftItem,
  UserPreference,
  VisionProvider,
  WardrobeItem,
  WearHistoryEntry
} from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function buildRequestErrorMessage(status: number, rawText: string): string {
  try {
    const payload = JSON.parse(rawText) as Partial<ApiEnvelope<unknown>> & { detail?: string };
    if (typeof payload.error === "string" && payload.error.trim()) {
      return payload.error;
    }
    if (typeof payload.detail === "string" && payload.detail.trim()) {
      return payload.detail;
    }
  } catch {
    // 这里故意吞掉 JSON 解析异常。
    // 后端在异常场景下不一定总能返回 JSON，
    // 因此前端需要退回到原始文本，而不是因为二次解析失败把真实错误覆盖掉。
  }

  if (rawText.trim()) {
    return rawText;
  }
  return `请求失败：${status}`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: {
        ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        ...init?.headers
      },
      ...init
    });
  } catch (error) {
    throw new Error(
      error instanceof Error && error.message
        ? `后端连接失败：${error.message}`
        : "后端连接失败，请确认服务是否正常运行。"
    );
  }

  if (!response.ok) {
    const text = await response.text();
    throw new Error(buildRequestErrorMessage(response.status, text));
  }

  const envelope = (await response.json()) as ApiEnvelope<T>;
  if (!envelope.success) {
    throw new Error(envelope.error ?? "请求失败");
  }
  return envelope.data;
}

export function resolveAssetUrl(path?: string | null): string {
  if (!path) {
    return "";
  }
  return path.startsWith("http") ? path : `${API_BASE}${path}`;
}

export const api = {
  getWardrobe(params?: Record<string, string | boolean | undefined>) {
    const query = new URLSearchParams();
    Object.entries(params ?? {}).forEach(([key, value]) => {
      if (value !== undefined && value !== "") {
        query.set(key, String(value));
      }
    });
    return request<{ items: WardrobeItem[] }>(`/api/wardrobe?${query.toString()}`);
  },

  updateWardrobeItem(itemId: string, payload: Partial<WardrobeItem>) {
    return request<WardrobeItem>(`/api/wardrobe/${itemId}`, {
      method: "PUT",
      body: JSON.stringify(payload)
    });
  },

  confirmWardrobeItem(itemId: string, updates: Partial<WardrobeItem>) {
    return request<WardrobeItem>(`/api/wardrobe/${itemId}/confirm`, {
      method: "POST",
      body: JSON.stringify({ updates })
    });
  },

  deleteWardrobeItem(itemId: string) {
    return request<{ deleted: boolean }>(`/api/wardrobe/${itemId}`, {
      method: "DELETE"
    });
  },

  uploadWardrobeItem(file: File, visionProvider: VisionProvider) {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("vision_provider", visionProvider);
    return request<UploadDraftItem>("/api/upload", {
      method: "POST",
      body: formData
    });
  },

  getForgottenItems() {
    return request<{ items: ForgottenItem[] }>("/api/forgotten");
  },

  getHistory() {
    return request<{ items: WearHistoryEntry[] }>("/api/history");
  },

  createHistory(payload: {
    item_ids: string[];
    occasion: string;
    weather_snapshot: Record<string, unknown>;
    outfit_name?: string;
    user_feedback?: string;
  }) {
    return request<WearHistoryEntry>("/api/history", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },

  getPreferences() {
    return request<{ preference: UserPreference }>("/api/preferences");
  },

  updatePreferences(payload: Partial<UserPreference>) {
    return request<{ preference: UserPreference }>("/api/preferences", {
      method: "PUT",
      body: JSON.stringify(payload)
    });
  },

  chat(message: string, history: ChatMessage[]) {
    return request<ChatResponseData>("/api/chat", {
      method: "POST",
      body: JSON.stringify({
        message,
        history: history.map(({ role, content }) => ({ role, content }))
      })
    });
  },

  getRecommendations(scenario: string, weatherMessage: string) {
    const query = new URLSearchParams({
      scenario,
      weather_message: weatherMessage
    });
    return request<{ items: OutfitRecommendation[] }>(`/api/recommendations?${query.toString()}`);
  }
};
