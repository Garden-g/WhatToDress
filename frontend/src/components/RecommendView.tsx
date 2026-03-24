import { CheckCircle2, Loader2, Sparkles } from "lucide-react";
import { useDeferredValue, useState } from "react";

import { api } from "../api/client";
import type { ForgottenItem, OutfitRecommendation, WeatherSnapshot } from "../types";
import { ItemCard } from "./ItemCard";
import { WeatherCard } from "./WeatherCard";

const SCENARIOS = ["日常上班", "周末逛街", "浪漫约会", "运动健身", "晚宴聚会"];

interface RecommendViewProps {
  forgottenItems: ForgottenItem[];
  onAccepted: (outfit: OutfitRecommendation, weather: WeatherSnapshot | null, scenario: string) => Promise<void>;
}

export function RecommendView({ forgottenItems, onAccepted }: RecommendViewProps) {
  const [scenario, setScenario] = useState("日常上班");
  const [weatherText, setWeatherText] = useState("今天 18 度");
  const [styleHint, setStyleHint] = useState("");
  const [results, setResults] = useState<OutfitRecommendation[]>([]);
  const [weather, setWeather] = useState<WeatherSnapshot | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const deferredResults = useDeferredValue(results);

  async function handleGenerate() {
    try {
      setError(null);
      setIsGenerating(true);
      const response = await api.getRecommendations(scenario, `${weatherText} ${styleHint}`.trim());
      setResults(response.items);
      setWeather((response.items[0]?.metadata.weather as WeatherSnapshot | undefined) ?? null);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "生成推荐失败");
    } finally {
      setIsGenerating(false);
    }
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <WeatherCard weather={weather} />

      <section className="bg-[rgba(255,255,255,0.76)] rounded-[2rem] p-6 md:p-8 shadow-sm border border-[color:var(--line)]">
        <h3 className="text-lg font-bold mb-6 flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-[color:var(--ink)]" />
          告诉 AI 你今天要去哪里
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div>
            <label className="block text-sm font-semibold text-[color:var(--ink)] mb-3">场景</label>
            <div className="flex flex-wrap gap-2">
              {SCENARIOS.map((item) => (
                <button
                  key={item}
                  onClick={() => setScenario(item)}
                  className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                    scenario === item
                      ? "bg-[color:rgba(44,36,29,0.95)] text-white shadow-md scale-105"
                      : "bg-[rgba(157,111,61,0.08)] text-[color:var(--muted)] hover:bg-[rgba(157,111,61,0.15)]"
                  }`}
                >
                  {item}
                </button>
              ))}
            </div>
          </div>
          <div className="space-y-4">
            <label className="block text-sm font-semibold text-[color:var(--ink)]">
              天气描述
              <input
                type="text"
                value={weatherText}
                onChange={(event) => setWeatherText(event.target.value)}
                placeholder="例如：明天 18 度下雨"
                className="mt-2 w-full bg-[rgba(244,238,228,0.7)] border border-[color:var(--line)] rounded-xl px-4 py-3 text-sm focus:outline-none"
              />
            </label>
            <label className="block text-sm font-semibold text-[color:var(--ink)]">
              风格补充
              <input
                type="text"
                value={styleHint}
                onChange={(event) => setStyleHint(event.target.value)}
                placeholder="例如：显瘦一点、深色、保暖优先"
                className="mt-2 w-full bg-[rgba(244,238,228,0.7)] border border-[color:var(--line)] rounded-xl px-4 py-3 text-sm focus:outline-none"
              />
            </label>
          </div>
        </div>

        <button
          onClick={() => void handleGenerate()}
          disabled={isGenerating}
          className="w-full bg-[color:rgba(44,36,29,0.95)] hover:bg-[color:rgba(44,36,29,0.85)] disabled:opacity-50 text-white font-bold py-4 rounded-2xl flex items-center justify-center gap-2 transition-all active:scale-[0.98]"
        >
          {isGenerating ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" /> 正在翻你的衣柜并计算穿搭...
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5" /> 一键帮我穿搭
            </>
          )}
        </button>
        {error && <p className="text-center text-red-500 text-sm mt-3 font-medium">{error}</p>}
      </section>

      {forgottenItems.length > 0 && (
        <section className="space-y-4">
          <div>
            <h3 className="text-xl font-black">先别急着买新衣服</h3>
            <p className="text-sm text-[color:var(--muted)] mt-1">这些单品已经很久没被你召回了，推荐时会优先考虑它们。</p>
          </div>
          <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-4">
            {forgottenItems.slice(0, 4).map((entry) => (
              <div key={entry.item.item_id} className="space-y-2">
                <ItemCard item={entry.item} />
                <div className="rounded-[1.25rem] bg-[rgba(157,111,61,0.08)] border border-[color:var(--line)] p-3 text-xs text-[color:var(--ink)]">
                  遗忘分：{entry.forgotten_score}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {deferredResults.length > 0 && (
        <section className="space-y-6 animate-in slide-in-from-bottom-8 duration-700">
          <h3 className="text-xl font-black px-2">AI 为你选出 3 套方案</h3>
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            {deferredResults.map((recommendation, index) => (
              <article
                key={recommendation.outfit_id}
                className="bg-[rgba(255,255,255,0.8)] rounded-[2rem] p-5 shadow-sm border border-[color:var(--line)] flex flex-col hover:shadow-md transition-shadow"
              >
                <div className="flex items-center justify-between mb-4">
                  <span className="bg-[rgba(157,111,61,0.08)] text-[color:var(--accent)] text-xs font-bold px-3 py-1 rounded-full">
                    方案 {index + 1}
                  </span>
                  <h4 className="font-bold text-lg">{recommendation.name}</h4>
                </div>

                <div className="grid grid-cols-2 gap-2 mb-4">
                  {recommendation.items.map((item) => (
                    <ItemCard key={item.item_id} item={item} compact />
                  ))}
                </div>

                <div className="flex-1 space-y-3 mb-6">
                  <p className="text-sm text-[color:var(--ink)] leading-relaxed">
                    <span className="font-semibold">为什么选这套：</span>
                    {recommendation.reason}
                  </p>
                  <p className="text-xs text-[color:var(--accent)] bg-[rgba(157,111,61,0.08)] p-3 rounded-xl font-medium">
                    {recommendation.tips}
                  </p>
                </div>

                <button
                  onClick={() => void onAccepted(recommendation, weather, scenario)}
                  className="w-full py-3 rounded-xl font-bold bg-[rgba(44,36,29,0.08)] hover:bg-[color:rgba(44,36,29,0.95)] hover:text-white transition-colors flex justify-center items-center gap-2 group"
                >
                  <CheckCircle2 className="w-4 h-4 group-hover:scale-110 transition-transform" />
                  就穿这套出门
                </button>
              </article>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

