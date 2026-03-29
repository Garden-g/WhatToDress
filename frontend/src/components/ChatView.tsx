import { ChevronDown, ChevronRight, Loader2, SendHorizontal } from "lucide-react";
import { type ReactNode, useCallback, useEffect, useRef, useState } from "react";

import { api } from "../api/client";
import type { ChatMessage, ChatStreamCallbacks, OutfitRecommendation, WardrobeItem, WeatherSnapshot } from "../types";
import { ItemCard } from "./ItemCard";

/**
 * 可折叠面板组件 —— 用于包裹「思考过程」或「工具调用」等区块
 * @param title       标题文字（始终可见）
 * @param children    折叠/展开的内容
 * @param defaultOpen 是否默认展开，默认 false
 */
function Collapsible({ title, children, defaultOpen = false }: {
  title: ReactNode;
  children: ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="mb-2">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1 text-xs text-[color:var(--muted)] hover:text-[color:var(--ink)] transition-colors"
      >
        {open ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
        {title}
      </button>
      {open && <div className="mt-1.5 ml-4">{children}</div>}
    </div>
  );
}

/** 阶段描述映射 */
const PHASE_LABELS: Record<string, string> = {
  planning: "正在思考...",
  executing: "正在查询...",
  summarizing: "正在整理...",
};

/** 工具执行状态图标 */
const TOOL_STATUS_ICON: Record<string, string> = {
  running: "⏳",
  done: "✅",
  error: "❌",
};

interface ChatViewProps {
  onAccepted: (outfit: OutfitRecommendation, weather: WeatherSnapshot | null, scenario: string) => Promise<void>;
}

function isWardrobeCard(card: unknown): card is WardrobeItem {
  return (
    typeof card === "object" &&
    card !== null &&
    "item_id" in card &&
    "category" in card
  );
}

function isRecommendationCard(card: unknown): card is OutfitRecommendation {
  return (
    typeof card === "object" &&
    card !== null &&
    "items" in card &&
    "reason" in card
  );
}

export function ChatView({ onAccepted }: ChatViewProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: "你可以直接问我：我有什么蓝色衬衫？或者 明天 18 度通勤穿什么？"
    }
  ]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);

  // 用于自动滚动到底部
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  /**
   * 更新「最后一条助手消息」的某些字段。
   * 在 SSE 流式过程中会被频繁调用来追加 thinking、更新状态等。
   */
  const updateLastAssistant = useCallback(
    (updater: (prev: ChatMessage) => Partial<ChatMessage>) => {
      setMessages((current) => {
        const copy = [...current];
        const lastIdx = copy.length - 1;
        if (lastIdx >= 0 && copy[lastIdx].role === "assistant") {
          copy[lastIdx] = { ...copy[lastIdx], ...updater(copy[lastIdx]) };
        }
        return copy;
      });
    },
    []
  );

  async function handleSend() {
    if (!input.trim() || isSending) return;

    const userText = input.trim();
    const nextUserMessage: ChatMessage = { role: "user", content: userText };
    const nextHistory = [...messages, nextUserMessage];
    setMessages(nextHistory);
    setInput("");
    setIsSending(true);

    // 先插入一条空的助手消息占位，后续通过 updateLastAssistant 增量填充
    setMessages((current) => [
      ...current,
      {
        role: "assistant",
        content: "",
        thinking: "",
        toolCallsInfo: undefined,
        toolStatuses: {},
        streamPhase: "planning",
      }
    ]);

    const callbacks: ChatStreamCallbacks = {
      onStage(phase) {
        updateLastAssistant(() => ({ streamPhase: phase as ChatMessage["streamPhase"] }));
      },

      onThinking(text) {
        updateLastAssistant((prev) => ({
          thinking: (prev.thinking ?? "") + text,
        }));
      },

      onToolCalls(tools) {
        updateLastAssistant(() => ({
          toolCallsInfo: tools,
          toolStatuses: Object.fromEntries(tools.map((t) => [t.name, "running" as const])),
        }));
      },

      onToolStatus(name, status) {
        updateLastAssistant((prev) => ({
          toolStatuses: {
            ...prev.toolStatuses,
            [name]: status as "running" | "done" | "error",
          },
        }));
      },

      onReply(text) {
        updateLastAssistant(() => ({ content: text }));
      },

      onCards(cards, action) {
        updateLastAssistant(() => ({
          cards,
          action: action as ChatMessage["action"],
        }));
      },

      onDone() {
        updateLastAssistant(() => ({ streamPhase: "done" }));
        setIsSending(false);
      },

      onError(errorMessage) {
        updateLastAssistant((prev) => ({
          content: prev.content || errorMessage,
          streamPhase: "done",
        }));
        setIsSending(false);
      },
    };

    try {
      await api.chatStream(userText, nextHistory, callbacks);
    } catch (error) {
      updateLastAssistant(() => ({
        content: error instanceof Error ? error.message : "聊天请求失败",
        streamPhase: "done",
      }));
      setIsSending(false);
    }
  }

  /** 判断一条消息是否仍在流式接收中 */
  const isStreaming = (msg: ChatMessage) =>
    msg.role === "assistant" && msg.streamPhase && msg.streamPhase !== "done";

  return (
    <section className="grid lg:grid-cols-[0.95fr_1.05fr] gap-6 items-start">
      <div className="bg-[rgba(255,255,255,0.82)] rounded-[2rem] border border-[color:var(--line)] overflow-hidden">
        <div className="p-5 border-b border-[color:var(--line)]">
          <h2 className="text-xl font-bold">对话问衣</h2>
          <p className="text-sm text-[color:var(--muted)] mt-1">把自然语言当筛选器，也可以直接把它当穿搭顾问。</p>
        </div>
        <div className="p-5 space-y-4 max-h-[65vh] overflow-y-auto thin-scrollbar">
          {messages.map((message, index) => (
            <div
              key={`${message.role}-${index}`}
              className={`rounded-[1.5rem] p-4 ${
                message.role === "assistant"
                  ? "bg-[rgba(157,111,61,0.08)] text-[color:var(--ink)]"
                  : "bg-[rgba(44,36,29,0.95)] text-white ml-auto max-w-[85%]"
              }`}
            >
              {/* ── 助手消息：思考过程（流式时展开，完成后折叠） ── */}
              {message.role === "assistant" && message.thinking && (
                <Collapsible
                  title={
                    <span className="flex items-center gap-1">
                      💭 思考过程
                      {isStreaming(message) && <Loader2 className="w-3 h-3 animate-spin" />}
                    </span>
                  }
                  defaultOpen={isStreaming(message)}
                >
                  <pre className="text-xs leading-5 whitespace-pre-wrap break-words text-[color:var(--muted)] bg-[rgba(157,111,61,0.06)] rounded-xl p-3 max-h-60 overflow-y-auto thin-scrollbar">
                    {message.thinking}
                  </pre>
                </Collapsible>
              )}

              {/* ── 助手消息：工具调用标签（含执行状态） ── */}
              {message.role === "assistant" && message.toolCallsInfo && message.toolCallsInfo.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {message.toolCallsInfo.map((tool, toolIndex) => {
                    const status = message.toolStatuses?.[tool.name];
                    const icon = status ? (TOOL_STATUS_ICON[status] ?? "🔧") : "🔧";
                    return (
                      <span
                        key={`tool-${toolIndex}`}
                        className="inline-flex items-center gap-1 text-xs bg-[rgba(157,111,61,0.12)] text-[color:var(--ink)] rounded-full px-2.5 py-0.5"
                      >
                        {icon} {tool.name}
                        {tool.arguments && Object.keys(tool.arguments).length > 0 && (
                          <span className="text-[color:var(--muted)]">
                            ({Object.entries(tool.arguments).map(([k, v]) => `${k}=${v}`).join(", ")})
                          </span>
                        )}
                      </span>
                    );
                  })}
                </div>
              )}

              {/* ── 流式阶段指示器 ── */}
              {isStreaming(message) && !message.content && (
                <div className="inline-flex items-center gap-2 text-sm text-[color:var(--muted)]">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  {PHASE_LABELS[message.streamPhase ?? ""] ?? "处理中..."}
                </div>
              )}

              {/* ── 回复正文 ── */}
              {message.content && (
                <p className="text-sm leading-7">{message.content}</p>
              )}
            </div>
          ))}
          {/* 自动滚动锚点 */}
          <div ref={chatEndRef} />
        </div>
        <div className="p-5 border-t border-[color:var(--line)]">
          <div className="flex gap-3">
            <input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  void handleSend();
                }
              }}
              placeholder="例如：我有什么蓝色衬衫"
              className="flex-1 rounded-2xl border border-[color:var(--line)] px-4 py-3 bg-[rgba(244,238,228,0.7)]"
            />
            <button
              onClick={() => void handleSend()}
              className="w-12 h-12 rounded-2xl bg-[color:rgba(44,36,29,0.95)] text-white inline-flex items-center justify-center"
            >
              <SendHorizontal className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <div>
          <h3 className="text-xl font-black">结果面板</h3>
          <p className="text-sm text-[color:var(--muted)] mt-1">这里会展示衣物卡片或穿搭方案，方便你继续操作。</p>
        </div>

        {messages
          .filter((message) => message.cards?.length)
          .slice(-1)
          .flatMap((message) => message.cards ?? [])
          .map((card, index) => {
            if (isWardrobeCard(card)) {
              return <ItemCard key={`item-${card.item_id}-${index}`} item={card} />;
            }
            if (isRecommendationCard(card)) {
              return (
                <article
                  key={`outfit-${card.outfit_id}-${index}`}
                  className="bg-[rgba(255,255,255,0.8)] rounded-[2rem] p-5 shadow-sm border border-[color:var(--line)] space-y-4"
                >
                  <div className="flex items-center justify-between">
                    <h4 className="font-bold text-lg">{card.name}</h4>
                    <span className="text-xs px-3 py-1 rounded-full bg-[rgba(157,111,61,0.08)] text-[color:var(--accent)]">
                      {card.scenario}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    {card.items.map((item) => (
                      <ItemCard key={item.item_id} item={item} compact />
                    ))}
                  </div>
                  <p className="text-sm leading-7">{card.reason}</p>
                  <button
                    onClick={() =>
                      void onAccepted(card, (card.metadata.weather as WeatherSnapshot | undefined) ?? null, card.scenario)
                    }
                    className="w-full py-3 rounded-xl font-bold bg-[rgba(44,36,29,0.08)] hover:bg-[color:rgba(44,36,29,0.95)] hover:text-white transition-colors"
                  >
                    就穿这套出门
                  </button>
                </article>
              );
            }

            return (
              <pre
                key={`raw-${index}`}
                className="bg-[rgba(255,255,255,0.82)] border border-[color:var(--line)] rounded-[1.5rem] p-4 text-xs overflow-auto"
              >
                {JSON.stringify(card, null, 2)}
              </pre>
            );
          })}
      </div>
    </section>
  );
}
