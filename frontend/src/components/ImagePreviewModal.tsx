import { X } from "lucide-react";
import { useEffect } from "react";

import { resolveAssetUrl } from "../api/client";
import type { WardrobeItem } from "../types";

interface ImagePreviewModalProps {
  item: WardrobeItem | null;
  onClose: () => void;
}

export function ImagePreviewModal({ item, onClose }: ImagePreviewModalProps) {
  useEffect(() => {
    if (!item) {
      return;
    }

    function handleKeydown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    window.addEventListener("keydown", handleKeydown);
    return () => window.removeEventListener("keydown", handleKeydown);
  }, [item, onClose]);

  if (!item) {
    return null;
  }

  const imageUrl = resolveAssetUrl(item.image_white_bg_url || item.image_original_url);
  const itemName = item.name || item.subcategory || item.category;

  return (
    <div
      className="fixed inset-0 z-[140] bg-[rgba(31,24,18,0.72)] backdrop-blur-md p-4 md:p-8 overflow-y-auto"
      onClick={onClose}
    >
      <div
        className="min-h-full flex items-center justify-center"
      >
        <div
          className="w-full max-w-5xl bg-[rgba(248,243,236,0.98)] border border-[color:var(--line)] rounded-[2rem] shadow-[0_24px_80px_rgba(0,0,0,0.28)] overflow-hidden"
          onClick={(event) => event.stopPropagation()}
        >
          <div className="flex items-center justify-between px-5 md:px-7 py-4 border-b border-[color:var(--line)]">
            <div className="min-w-0">
              <p className="text-xs font-black uppercase tracking-[0.28em] text-[color:rgba(132,115,98,0.72)]">
                图片预览
              </p>
              <h3 className="mt-2 text-xl md:text-2xl font-black truncate">{itemName}</h3>
            </div>
            <button
              onClick={onClose}
              className="w-11 h-11 rounded-full bg-[rgba(157,111,61,0.1)] hover:bg-[rgba(157,111,61,0.16)] inline-flex items-center justify-center transition-colors shrink-0"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="grid lg:grid-cols-[minmax(0,1.35fr)_minmax(320px,0.75fr)]">
            <div className="bg-[linear-gradient(180deg,rgba(255,255,255,0.6),rgba(236,228,216,0.92))] p-4 md:p-8">
              <div className="rounded-[1.75rem] overflow-hidden border border-[rgba(92,73,55,0.1)] bg-white shadow-[0_20px_40px_rgba(67,52,38,0.12)]">
                <img
                  src={imageUrl}
                  alt={itemName}
                  className="w-full max-h-[72vh] object-contain bg-[radial-gradient(circle_at_top,rgba(157,111,61,0.08),transparent_48%),linear-gradient(180deg,#fdfbf8_0%,#f2e9dd_100%)]"
                />
              </div>
            </div>

            <div className="p-5 md:p-7 bg-[rgba(255,251,246,0.72)]">
              <div className="rounded-[1.5rem] border border-[color:var(--line)] bg-white/80 p-4 md:p-5 space-y-4">
                <div>
                  <p className="text-xs font-black uppercase tracking-[0.24em] text-[color:rgba(132,115,98,0.72)]">
                    基础信息
                  </p>
                  <p className="mt-3 text-base font-bold">{item.category}</p>
                  <p className="mt-1 text-sm text-[color:var(--muted)]">
                    {item.subcategory || "未补充子分类"}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-2xl bg-[color:var(--paper)] p-3">
                    <p className="text-xs text-[color:var(--muted)]">颜色</p>
                    <p className="mt-1 font-bold">{item.color}</p>
                  </div>
                  <div className="rounded-2xl bg-[color:var(--paper)] p-3">
                    <p className="text-xs text-[color:var(--muted)]">区域</p>
                    <p className="mt-1 font-bold">{item.closet_section}</p>
                  </div>
                </div>

                <div>
                  <p className="text-xs text-[color:var(--muted)] mb-2">风格</p>
                  <div className="flex flex-wrap gap-2">
                    {(item.style_tags.length > 0 ? item.style_tags : ["未标注风格"]).map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center px-3 py-1.5 rounded-full bg-[rgba(157,111,61,0.12)] text-[color:var(--ink)] text-xs font-bold"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="rounded-[1.25rem] border border-dashed border-[rgba(157,111,61,0.28)] bg-[rgba(157,111,61,0.05)] p-3">
                  <p className="text-xs font-semibold text-[color:var(--muted)]">
                    这张大图默认沿用衣柜卡片当前显示的图片来源。
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
