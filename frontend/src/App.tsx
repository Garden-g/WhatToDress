import { useEffect, useState } from "react";

import { api } from "./api/client";
import { ChatView } from "./components/ChatView";
import { HistoryView } from "./components/HistoryView";
import { Layout } from "./components/Layout";
import { RecommendView } from "./components/RecommendView";
import { WardrobeView } from "./components/WardrobeView";
import type {
  ForgottenItem,
  OutfitRecommendation,
  TabKey,
  UserPreference,
  WardrobeItem,
  WearHistoryEntry,
  WeatherSnapshot
} from "./types";

export default function App() {
  const [activeTab, setActiveTab] = useState<TabKey>("recommend");
  const [wardrobeItems, setWardrobeItems] = useState<WardrobeItem[]>([]);
  const [forgottenItems, setForgottenItems] = useState<ForgottenItem[]>([]);
  const [history, setHistory] = useState<WearHistoryEntry[]>([]);
  const [preferences, setPreferences] = useState<UserPreference | null>(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadAllData() {
    try {
      setError(null);
      setIsBootstrapping(true);
      const [wardrobe, forgotten, historyResponse, preferenceResponse] = await Promise.all([
        api.getWardrobe(),
        api.getForgottenItems(),
        api.getHistory(),
        api.getPreferences()
      ]);
      setWardrobeItems(wardrobe.items.filter((item) => item.confirmed));
      setForgottenItems(forgotten.items);
      setHistory(historyResponse.items);
      setPreferences(preferenceResponse.preference);
    } catch (bootstrapError) {
      setError(bootstrapError instanceof Error ? bootstrapError.message : "初始化失败");
    } finally {
      setIsBootstrapping(false);
    }
  }

  useEffect(() => {
    void loadAllData();
  }, []);

  async function handleDeleteItem(itemId: string) {
    await api.deleteWardrobeItem(itemId);
    await loadAllData();
  }

  async function handleAcceptedRecommendation(
    outfit: OutfitRecommendation,
    weather: WeatherSnapshot | null,
    scenario: string
  ) {
    await api.createHistory({
      item_ids: outfit.items.map((item) => item.item_id),
      occasion: scenario,
      weather_snapshot: weather ? { ...weather } : {},
      outfit_name: outfit.name
    });
    await loadAllData();
    setActiveTab("history");
  }

  return (
    <Layout activeTab={activeTab} onTabChange={setActiveTab}>
      <section className="mb-8">
        <p className="display-title text-5xl md:text-6xl font-semibold leading-none">穿搭不该只靠临时发挥</p>
        <p className="mt-4 max-w-3xl text-[color:var(--muted)] leading-7">
          这个版本先把“拍照入库、自然语言检索、遗忘召回、穿搭推荐、穿着记录”全部打通。
          {preferences && preferences.preferred_styles.length > 0
            ? ` 当前偏好风格：${preferences.preferred_styles.join(" / ")}。`
            : " 你还没设置太多偏好，所以系统会更依赖衣柜状态和天气。"}
        </p>
      </section>

      {error && (
        <div className="mb-6 rounded-[1.5rem] border border-red-200 bg-red-50 p-4 text-red-700">{error}</div>
      )}

      {isBootstrapping ? (
        <div className="rounded-[2rem] border border-[color:var(--line)] bg-[rgba(255,255,255,0.72)] p-12 text-center text-[color:var(--muted)]">
          正在读取衣柜、历史和偏好数据...
        </div>
      ) : null}

      {!isBootstrapping && activeTab === "recommend" && (
        <RecommendView forgottenItems={forgottenItems} onAccepted={handleAcceptedRecommendation} />
      )}

      {!isBootstrapping && activeTab === "chat" && (
        <ChatView onAccepted={handleAcceptedRecommendation} />
      )}

      {!isBootstrapping && activeTab === "wardrobe" && (
        <WardrobeView
          items={wardrobeItems}
          isRefreshing={isBootstrapping}
          onDelete={handleDeleteItem}
          onUploaded={loadAllData}
        />
      )}

      {!isBootstrapping && activeTab === "history" && (
        <HistoryView history={history} wardrobeItems={wardrobeItems} />
      )}
    </Layout>
  );
}
