import type {
  ApiEnvelope,
  ChatMessage,
  ChatStreamCallbacks,
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

  /**
   * SSE 流式对话接口 —— 通过回调逐步推送事件
   *
   * 后端返回 SSE 流，事件类型包括：
   *   stage      → 当前阶段 (planning/executing/summarizing)
   *   thinking   → 思维链 chunk
   *   tool_calls → 工具调用信息
   *   tool_status→ 工具执行状态
   *   reply      → 最终回复文本
   *   cards      → 卡片数据 + action
   *   done       → 结束
   *   error      → 错误
   */
  async chatStream(
    message: string,
    history: ChatMessage[],
    callbacks: ChatStreamCallbacks,
    imageBase64?: string,
    imageMimeType?: string,
  ): Promise<void> {
    const response = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        history: history.map(({ role, content }) => ({ role, content })),
        image_base64: imageBase64 ?? null,
        image_mime_type: imageMimeType ?? null,
      })
    });

    if (!response.ok || !response.body) {
      const text = await response.text();
      callbacks.onError?.(buildRequestErrorMessage(response.status, text));
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    // 逐行解析 SSE
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      // 最后一个元素可能是不完整的行，保留在 buffer 中
      buffer = lines.pop() ?? "";

      let currentEvent = "";
      for (const line of lines) {
        if (line.startsWith("event: ")) {
          currentEvent = line.slice(7).trim();
        } else if (line.startsWith("data: ") && currentEvent) {
          try {
            const data = JSON.parse(line.slice(6)) as Record<string, unknown>;
            this._dispatchSSE(currentEvent, data, callbacks);
          } catch {
            // 忽略无法解析的行
          }
          currentEvent = "";
        } else if (line.trim() === "") {
          currentEvent = "";
        }
      }
    }
  },

  /** 内部方法：根据 SSE 事件类型分发回调 */
  _dispatchSSE(
    eventType: string,
    data: Record<string, unknown>,
    cb: ChatStreamCallbacks
  ) {
    switch (eventType) {
      case "stage":
        cb.onStage?.(data.phase as string);
        break;
      case "thinking":
        cb.onThinking?.(data.text as string, data.phase as string);
        break;
      case "tool_calls":
        cb.onToolCalls?.(data.tools as Array<{ name: string; arguments: Record<string, unknown> }>);
        break;
      case "tool_status":
        cb.onToolStatus?.(data.name as string, data.status as string);
        break;
      case "reply":
        cb.onReply?.(data.text as string);
        break;
      case "cards":
        cb.onCards?.(data.cards as Array<Record<string, unknown>>, data.action as string);
        break;
      case "done":
        cb.onDone?.();
        break;
      case "error":
        cb.onError?.(data.message as string);
        break;
      case "image_analyzed":
        cb.onImageAnalyzed?.(data.image_url as string, data.summary as string);
        break;
    }
  },

  getRecommendations(scenario: string, weatherMessage: string) {
    const query = new URLSearchParams({
      scenario,
      weather_message: weatherMessage
    });
    return request<{ items: OutfitRecommendation[] }>(`/api/recommendations?${query.toString()}`);
  }
};
