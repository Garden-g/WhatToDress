import { CheckCircle2, CloudSun, History } from "lucide-react";

import type { WardrobeItem, WearHistoryEntry } from "../types";
import { ItemCard } from "./ItemCard";

interface HistoryViewProps {
  history: WearHistoryEntry[];
  wardrobeItems: WardrobeItem[];
}

export function HistoryView({ history, wardrobeItems }: HistoryViewProps) {
  const itemMap = new Map(wardrobeItems.map((item) => [item.item_id, item]));

  if (history.length === 0) {
    return (
      <div className="max-w-4xl mx-auto animate-in fade-in duration-500">
        <h2 className="text-2xl font-black mb-8 flex items-center gap-2">
          <History className="w-6 h-6" /> 穿搭时光机
        </h2>
        <div className="text-center py-20 bg-[rgba(255,255,255,0.78)] rounded-[2rem] border border-[color:var(--line)]">
          <History className="w-12 h-12 text-[color:rgba(132,115,98,0.3)] mx-auto mb-4" />
          <p className="text-[color:var(--muted)] font-medium">还没记录过穿搭呢。去让 AI 帮你配一套吧。</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto animate-in fade-in duration-500">
      <h2 className="text-2xl font-black mb-8 flex items-center gap-2">
        <History className="w-6 h-6" /> 穿搭时光机
      </h2>

      <div className="space-y-8 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-[rgba(132,115,98,0.24)] before:to-transparent">
        {history.map((entry) => {
          const items = entry.item_ids
            .map((itemId) => itemMap.get(itemId))
            .filter((item): item is WardrobeItem => Boolean(item));

          return (
            <div
              key={entry.log_id}
              className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group"
            >
              <div className="flex items-center justify-center w-10 h-10 rounded-full border-4 border-[#fbf5ea] bg-[color:rgba(44,36,29,0.95)] text-white shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow-sm z-10">
                <CheckCircle2 className="w-5 h-5" />
              </div>

              <div className="w-[calc(100%-4rem)] md:w-[calc(50%-3rem)] bg-[rgba(255,255,255,0.82)] p-5 rounded-[2rem] shadow-sm border border-[color:var(--line)] hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-bold text-[color:var(--muted)]">{new Date(entry.date).toLocaleString()}</span>
                  <span className="text-xs bg-[rgba(157,111,61,0.08)] px-2 py-1 rounded-md font-medium text-[color:var(--accent)]">
                    {entry.occasion}
                  </span>
                </div>
                <p className="text-sm text-[color:var(--ink)] mb-4 flex items-center gap-1.5 bg-[rgba(157,111,61,0.06)] p-2 rounded-xl">
                  <CloudSun className="w-4 h-4" /> {String(entry.weather_snapshot.city ?? "默认城市")} ·{" "}
                  {String(entry.weather_snapshot.temp ?? "--")}°C
                </p>
                <div className="flex gap-2 overflow-x-auto pb-2 thin-scrollbar">
                  {items.map((item) => (
                    <ItemCard key={item.item_id} item={item} compact />
                  ))}
                </div>
                <p className="text-sm font-bold mt-3">✨ {entry.outfit_name || "已记录穿搭"}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

