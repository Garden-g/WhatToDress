import { CloudRain, MapPin, Thermometer, Wind } from "lucide-react";

import type { WeatherSnapshot } from "../types";

interface WeatherCardProps {
  weather: WeatherSnapshot | null;
}

export function WeatherCard({ weather }: WeatherCardProps) {
  if (!weather) {
    return (
      <div className="bg-[rgba(255,255,255,0.72)] rounded-[2rem] p-6 border border-[color:var(--line)]">
        <p className="text-sm text-[color:var(--muted)]">
          输入温度或场景后，我会把天气信息和穿搭建议一起展示在这里。
        </p>
      </div>
    );
  }

  return (
    <div className="bg-[rgba(255,255,255,0.76)] rounded-[2rem] p-6 shadow-sm border border-[color:var(--line)] flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
      <div className="flex items-center gap-4">
        <div className="p-4 bg-[color:var(--accent-soft)] rounded-2xl">
          <CloudRain className="w-8 h-8 text-[color:var(--accent)]" />
        </div>
        <div>
          <div className="flex items-center gap-2 text-[color:var(--muted)] text-sm font-medium mb-1">
            <MapPin className="w-4 h-4" />
            {weather.city}
          </div>
          <h2 className="text-3xl font-bold flex items-center gap-2">
            {weather.temp}°C
            <span className="text-lg text-[color:var(--muted)] font-medium">
              / {weather.condition}
            </span>
          </h2>
        </div>
      </div>
      <div className="bg-[rgba(157,111,61,0.08)] px-4 py-3 rounded-2xl text-sm text-[color:var(--ink)] max-w-sm leading-relaxed border border-[color:var(--line)] space-y-1">
        <div className="flex items-center gap-2">
          <Thermometer className="w-4 h-4" />
          体感温区：{weather.temp_min}°C - {weather.temp_max}°C
        </div>
        <div className="flex items-center gap-2">
          <CloudRain className="w-4 h-4" />
          降雨概率：{weather.rain_probability}%
        </div>
        <div className="flex items-center gap-2">
          <Wind className="w-4 h-4" />
          最大风速：{weather.wind_speed}
        </div>
      </div>
    </div>
  );
}

