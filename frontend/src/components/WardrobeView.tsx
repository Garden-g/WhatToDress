import { Eye, Loader2, Plus, Trash2 } from "lucide-react";
import { useState } from "react";

import { resolveAssetUrl } from "../api/client";
import type { WardrobeItem } from "../types";
import { ImagePreviewModal } from "./ImagePreviewModal";
import { UploadModal } from "./UploadModal";

interface WardrobeViewProps {
  items: WardrobeItem[];
  isRefreshing: boolean;
  onDelete: (itemId: string) => Promise<void>;
  onUploaded: () => Promise<void>;
}

interface ClosetStripProps {
  items: WardrobeItem[];
  emptyText: string;
  onDelete: (itemId: string) => Promise<void>;
  onPreview: (item: WardrobeItem) => void;
  title: string;
  decorateWithClip?: boolean;
}

function renderClosetStrip({
  items,
  emptyText,
  onDelete,
  onPreview,
  title,
  decorateWithClip = false
}: ClosetStripProps) {
  return (
    <div className="mb-16 relative pt-4">
      <h3 className="text-xs font-bold text-[color:rgba(132,115,98,0.7)] uppercase tracking-[0.3em] mb-6 ml-2">
        {title}
      </h3>
      <div className="h-3.5 w-[110%] -ml-[5%] bg-gradient-to-b from-[#b8aa97] via-[#d4cabd] to-[#ab9982] rounded-full shadow-[0_4px_10px_rgba(0,0,0,0.15)] absolute top-[3.75rem] left-0 z-0" />
      <div className="flex gap-0.5 md:gap-1 overflow-x-auto pb-8 pt-4 px-4 relative z-10 min-h-[320px] items-start thin-scrollbar">
        {items.map((item) => (
          <div
            key={item.item_id}
            className="shrink-0 w-6 md:w-8 hover:w-48 md:hover:w-64 group relative transition-[width] duration-500 ease-[cubic-bezier(0.25,1,0.5,1)] cursor-zoom-in h-64 md:h-[19rem] z-10 hover:z-30"
          >
            <div className="w-4 md:w-5 h-8 border-t-[3px] border-r-[3px] border-[#b79f87] rounded-tr-full absolute -top-8 left-1/2 -translate-x-1/2 group-hover:border-[#8b735f] transition-colors z-20" />
            {decorateWithClip && (
              <div className="w-12 h-1.5 bg-[#b79f87] absolute -top-1 left-1/2 -translate-x-1/2 rounded-full z-20 group-hover:bg-[#8b735f] transition-colors shadow-sm" />
            )}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-48 md:w-64 h-full [perspective:1200px] pointer-events-none">
              <button
                type="button"
                onClick={() => onPreview(item)}
                className="w-full h-full rounded-xl md:rounded-2xl overflow-hidden shadow-[inset_2px_0_10px_rgba(0,0,0,0.2),5px_5px_15px_rgba(0,0,0,0.1)] group-hover:shadow-[0_15px_35px_rgba(0,0,0,0.25)] bg-[#ddd2c2] border border-[#d9cdbd] group-hover:border-[#f8f2e8] origin-center transition-transform duration-500 ease-[cubic-bezier(0.25,1,0.5,1)] [transform:rotateY(-80deg)] group-hover:[transform:rotateY(0deg)] pointer-events-auto relative text-left"
              >
                <img
                  src={resolveAssetUrl(item.image_white_bg_url || item.image_original_url)}
                  alt={item.category}
                  className="w-full h-full object-cover object-center"
                />
                <div className="absolute inset-0 bg-gradient-to-r from-black/60 via-black/20 to-transparent group-hover:opacity-0 transition-opacity duration-500 pointer-events-none" />
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 flex flex-col justify-between p-3 md:p-4 pointer-events-none">
                  <div className="flex items-start justify-between gap-2">
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-[rgba(255,255,255,0.92)] text-[color:var(--ink)] text-[10px] md:text-xs font-black shadow-sm">
                      <Eye className="w-3 h-3" />
                      点击看大图
                    </span>
                    <button
                      type="button"
                      onClick={(event) => {
                        event.preventDefault();
                        event.stopPropagation();
                        void onDelete(item.item_id);
                      }}
                      className="p-2 bg-red-500/90 text-white rounded-full hover:bg-red-600 hover:scale-110 transition-transform shadow-lg backdrop-blur-sm pointer-events-auto"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                  <div className="translate-y-4 group-hover:translate-y-0 transition-transform duration-500 ease-out whitespace-nowrap overflow-hidden">
                    <span className="inline-block px-2 py-1 bg-white text-[color:var(--ink)] text-[10px] md:text-xs font-black rounded mb-1.5 shadow-sm">
                      {item.category}
                    </span>
                    <p className="text-white/95 text-xs md:text-sm font-medium truncate">
                      {item.color} · {item.style_tags.join(" / ") || "未标注风格"}
                    </p>
                  </div>
                </div>
              </button>
            </div>
          </div>
        ))}
        {items.length === 0 && (
          <div className="w-full text-center py-10 text-[color:var(--muted)] text-sm font-medium">{emptyText}</div>
        )}
      </div>
    </div>
  );
}

export function WardrobeView({ items, isRefreshing, onDelete, onUploaded }: WardrobeViewProps) {
  const [openUpload, setOpenUpload] = useState(false);
  const [previewItem, setPreviewItem] = useState<WardrobeItem | null>(null);
  const hangingItems = items.filter((item) => item.closet_section === "top" || item.closet_section === "outerwear");
  const bottomItems = items.filter((item) => item.closet_section === "bottom");
  const shoeItems = items.filter((item) => item.closet_section === "shoes");

  return (
    <>
      <div className="animate-in fade-in duration-500">
        <div className="flex items-center justify-between mb-6 gap-4">
          <div>
            <h2 className="text-2xl font-black">我的数字衣柜</h2>
            <p className="text-sm text-[color:var(--muted)] mt-1">目前收录了 {items.length} 件已确认单品</p>
          </div>
          <button
            onClick={() => setOpenUpload(true)}
            className="bg-[color:rgba(44,36,29,0.95)] text-white px-4 py-2.5 rounded-xl text-sm font-bold hover:bg-[color:rgba(44,36,29,0.85)] transition-all active:scale-95 flex items-center gap-2 shadow-md"
          >
            {isRefreshing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
            <span>{isRefreshing ? "同步中..." : "购入新衣"}</span>
          </button>
        </div>

        <div className="bg-[color:var(--paper)] p-4 md:p-8 rounded-[2rem] border-[8px] border-[rgba(182,164,144,0.45)] shadow-wardrobe relative overflow-hidden">
          {renderClosetStrip({
            items: hangingItems,
            emptyText: "挂衣区还是空的，先去收几件上装。",
            onDelete,
            onPreview: setPreviewItem,
            title: "挂衣区 / HANGING"
          })}
          {renderClosetStrip({
            items: bottomItems,
            emptyText: "下装区还是空的，今天可能只剩上半身有穿搭了。",
            onDelete,
            onPreview: setPreviewItem,
            title: "下装区 / BOTTOMS",
            decorateWithClip: true
          })}

          <div className="relative">
            <h3 className="text-xs font-bold text-[color:rgba(132,115,98,0.7)] uppercase tracking-[0.3em] mb-6 ml-2">
              鞋架 / SHOES
            </h3>
            <div className="h-2 w-[110%] -ml-[5%] bg-[#d2c4b4] shadow-inner absolute bottom-4 left-0 z-0" />
            <div className="h-2 w-[110%] -ml-[5%] bg-[#b9a894] shadow-inner absolute bottom-8 left-0 z-0" />

            <div className="flex gap-6 md:gap-8 overflow-x-auto pb-4 px-2 thin-scrollbar relative z-10 items-end">
              {shoeItems.map((item) => (
                <button
                  type="button"
                  key={item.item_id}
                  onClick={() => setPreviewItem(item)}
                  className="snap-center shrink-0 w-28 md:w-32 group hover:-translate-y-2 hover:scale-110 transition-all duration-300 cursor-zoom-in text-left"
                >
                  <div className="aspect-[4/3] rounded-lg overflow-hidden shadow-md group-hover:shadow-2xl bg-white relative border border-[color:var(--line)]">
                    <img
                      src={resolveAssetUrl(item.image_white_bg_url || item.image_original_url)}
                      alt={item.category}
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-between p-2 backdrop-blur-[2px]">
                      <div className="flex items-start justify-between gap-2">
                        <span className="inline-flex items-center gap-1 px-1.5 py-1 bg-white/95 text-[color:var(--ink)] text-[10px] font-black rounded">
                          <Eye className="w-3 h-3" />
                          大图
                        </span>
                        <button
                          type="button"
                          onClick={(event) => {
                            event.preventDefault();
                            event.stopPropagation();
                            void onDelete(item.item_id);
                          }}
                          className="p-1.5 bg-red-500 text-white rounded-full hover:bg-red-600 hover:scale-110 transition-transform"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                      <div>
                        <span className="inline-block px-1.5 py-0.5 bg-white text-[color:var(--ink)] text-[10px] font-black rounded">
                          {item.category}
                        </span>
                      </div>
                    </div>
                  </div>
                </button>
              ))}
              {shoeItems.length === 0 && (
                <div className="w-full text-center py-10 text-[color:var(--muted)] text-sm font-medium">鞋架还空着。</div>
              )}
            </div>
          </div>
        </div>
      </div>

      <UploadModal
        open={openUpload}
        onClose={() => setOpenUpload(false)}
        onUploaded={async () => {
          await onUploaded();
          setOpenUpload(false);
        }}
      />

      <ImagePreviewModal item={previewItem} onClose={() => setPreviewItem(null)} />
    </>
  );
}
