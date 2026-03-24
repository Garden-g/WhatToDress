import { Shirt } from "lucide-react";

import { resolveAssetUrl } from "../api/client";
import type { WardrobeItem } from "../types";

interface ItemCardProps {
  item: WardrobeItem;
  compact?: boolean;
}

export function ItemCard({ item, compact = false }: ItemCardProps) {
  const imageUrl = resolveAssetUrl(item.image_white_bg_url || item.image_original_url);

  return (
    <article
      className={`bg-[rgba(255,255,255,0.82)] border border-[color:var(--line)] rounded-[1.5rem] overflow-hidden shadow-sm ${
        compact ? "w-24" : ""
      }`}
    >
      <div className={`${compact ? "aspect-square" : "aspect-[4/5]"} bg-[color:rgba(157,111,61,0.06)]`}>
        {imageUrl ? (
          <img src={imageUrl} alt={item.category} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-[color:var(--muted)]">
            <Shirt className="w-8 h-8" />
          </div>
        )}
      </div>
      {!compact && (
        <div className="p-4 space-y-2">
          <div className="flex items-center justify-between gap-3">
            <h3 className="font-bold text-sm">{item.name || item.category}</h3>
            {!item.confirmed && (
              <span className="text-[10px] px-2 py-1 rounded-full bg-amber-100 text-amber-700">
                待确认
              </span>
            )}
          </div>
          <p className="text-xs text-[color:var(--muted)]">
            {item.color} · {item.style_tags.join(" / ") || "未标注风格"}
          </p>
          <div className="flex flex-wrap gap-2">
            {item.season_tags.slice(0, 3).map((season) => (
              <span
                key={season}
                className="text-[10px] px-2 py-1 rounded-full bg-[rgba(157,111,61,0.1)] text-[color:var(--accent)]"
              >
                {season}
              </span>
            ))}
          </div>
        </div>
      )}
    </article>
  );
}

