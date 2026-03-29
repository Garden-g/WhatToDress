export type TabKey = "recommend" | "chat" | "wardrobe" | "history";
export type VisionProvider = "gemini" | "glm";

export interface WardrobeItem {
  item_id: string;
  name: string | null;
  category: string;
  subcategory: string | null;
  closet_section: "top" | "bottom" | "outerwear" | "shoes" | "accessory" | "other";
  color: string;
  secondary_color: string | null;
  season_tags: string[];
  style_tags: string[];
  formality: "casual" | "smart_casual" | "formal";
  material: string | null;
  brand: string | null;
  image_original_url: string;
  image_white_bg_url: string | null;
  is_available: boolean;
  clean_status: "clean" | "dirty" | "washing" | "ironing" | "storage";
  storage_location: string | null;
  last_worn_date: string | null;
  wear_count: number;
  favorite_score: number;
  dislike_flag: boolean;
  analysis_notes: string | null;
  confirmed: boolean;
  created_at: string;
  updated_at: string;
}

export interface ForgottenItem {
  item: WardrobeItem;
  forgotten_score: number;
  reasons: string[];
}

export interface OutfitRecommendation {
  outfit_id: string;
  name: string;
  items: WardrobeItem[];
  scenario: string;
  reason: string;
  tips: string;
  created_at: string;
  accepted_or_not: boolean | null;
  metadata: {
    has_forgotten_item?: boolean;
    weather?: WeatherSnapshot;
  };
}

export interface WearHistoryEntry {
  log_id: string;
  item_ids: string[];
  date: string;
  occasion: string;
  weather_snapshot: Record<string, unknown>;
  user_feedback: string | null;
  outfit_name: string | null;
  created_at: string;
}

export interface UserPreference {
  user_id: string;
  preferred_styles: string[];
  avoid_styles: string[];
  preferred_colors: string[];
  avoid_colors: string[];
  temperature_sensitivity: string;
  fit_preference: string;
  comfort_priority: string;
  formality_preference: string;
  updated_at: string;
}

export interface WeatherSnapshot {
  city: string;
  date: string;
  temp: number;
  temp_max: number;
  temp_min: number;
  rain_probability: number;
  wind_speed: number;
  condition: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  cards?: Array<Record<string, unknown>>;
  action?: "query" | "recommend" | "clarify" | "confirm";
  /** DeepSeek-R1 思维链文本（可折叠展示） */
  thinking?: string;
  /** 本次调用了哪些工具及参数摘要 */
  toolCallsInfo?: Array<{ name: string; arguments: Record<string, unknown> }>;
  /** 工具执行状态（流式更新） */
  toolStatuses?: Record<string, "running" | "done" | "error">;
  /** 当前流式阶段 */
  streamPhase?: "planning" | "executing" | "summarizing" | "analyzing_image" | "done";
  /** 用户发送的图片 URL（用于在聊天气泡中展示） */
  imageUrl?: string;
}

/** SSE 事件类型定义（后端推送的 event type） */
export type SSEEventType = "stage" | "thinking" | "tool_calls" | "tool_status" | "reply" | "cards" | "done" | "error" | "image_analyzed";

/** SSE 事件回调接口 */
export interface ChatStreamCallbacks {
  onStage?: (phase: string) => void;
  onThinking?: (text: string, phase: string) => void;
  onToolCalls?: (tools: Array<{ name: string; arguments: Record<string, unknown> }>) => void;
  onToolStatus?: (name: string, status: string) => void;
  onReply?: (text: string) => void;
  onCards?: (cards: Array<Record<string, unknown>>, action: string) => void;
  onDone?: () => void;
  onError?: (message: string) => void;
  /** 图片识别完成回调 */
  onImageAnalyzed?: (imageUrl: string, summary: string) => void;
}

export interface ChatResponseData {
  reply: string;
  cards: Array<Record<string, unknown>>;
  action: "query" | "recommend" | "clarify" | "confirm";
  thinking?: string | null;
  tool_calls_info?: Array<{ name: string; arguments: Record<string, unknown> }> | null;
}

export interface UploadDraftItem {
  item: WardrobeItem;
}

export interface ApiEnvelope<T> {
  success: boolean;
  data: T;
  error: string | null;
}
