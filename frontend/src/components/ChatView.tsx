import { Loader2, SendHorizontal } from "lucide-react";
import { useState } from "react";

import { api } from "../api/client";
import type { ChatMessage, OutfitRecommendation, WardrobeItem, WeatherSnapshot } from "../types";
import { ItemCard } from "./ItemCard";

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

  async function handleSend() {
    if (!input.trim()) {
      return;
    }

    const nextUserMessage: ChatMessage = { role: "user", content: input.trim() };
    const nextHistory = [...messages, nextUserMessage];
    setMessages(nextHistory);
    setInput("");

    try {
      setIsSending(true);
      const response = await api.chat(nextUserMessage.content, nextHistory);
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: response.reply,
          cards: response.cards,
          action: response.action
        }
      ]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: error instanceof Error ? error.message : "聊天请求失败"
        }
      ]);
    } finally {
      setIsSending(false);
    }
  }

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
              <p className="text-sm leading-7">{message.content}</p>
            </div>
          ))}
          {isSending && (
            <div className="rounded-[1.5rem] p-4 bg-[rgba(157,111,61,0.08)] text-[color:var(--ink)] inline-flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" /> 正在思考...
            </div>
          )}
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
